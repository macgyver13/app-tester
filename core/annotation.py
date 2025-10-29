"""
Screenshot annotation engine for adding visual markers to images
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from typing import List, Tuple, Optional

from .automation import Step, Annotation


class AnnotationEngine:
    """Engine for applying visual annotations to screenshots"""

    def __init__(self, font_path: Optional[str] = None, font_size: int = 30, display_scale: float = 1.0):
        self.font_size = font_size
        self.font = self._load_font(font_path, font_size)
        self.display_scale = display_scale  # Display scale factor (2.0 for retina, 1.0 for non-retina)
        
        # Color mappings (BGR for OpenCV, RGB for PIL)
        self.colors_bgr = {
            "red": (0, 0, 255),
            "blue": (255, 0, 0),
            "green": (0, 255, 0),
            "yellow": (0, 255, 255),
            "orange": (0, 165, 255),
            "purple": (255, 0, 255),
            "black": (0, 0, 0),
            "white": (255, 255, 255),
        }
        
        self.colors_rgb = {
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "green": (0, 255, 0),
            "yellow": (255, 255, 0),
            "orange": (255, 165, 0),
            "purple": (255, 0, 255),
            "black": (0, 0, 0),
            "white": (255, 255, 255),
        }
    
    def _load_font(self, font_path: Optional[str], size: int):
        """Load TrueType font or use default"""
        try:
            if font_path and Path(font_path).exists():
                return ImageFont.truetype(font_path, size)
            # Try common system fonts on macOS
            system_fonts = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/SFNSDisplay.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
            for font in system_fonts:
                if Path(font).exists():
                    return ImageFont.truetype(font, size)
        except Exception:
            pass
        
        return ImageFont.load_default()
    
    def annotate_step(self, step: Step, output_dir: Path) -> Optional[Path]:
        """Apply all annotations to a step's screenshot"""
        if not step.screenshot_path or not step.screenshot_path.exists():
            return None
        
        if not step.annotations:
            # No annotations needed, use original screenshot
            step.annotated_screenshot_path = step.screenshot_path
            return step.screenshot_path
        
        # Load image
        img = cv2.imread(str(step.screenshot_path))
        if img is None:
            print(f"Warning: Could not load screenshot: {step.screenshot_path}")
            return None
        
        # Convert to PIL for some operations
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Apply each annotation
        for annotation in step.annotations:
            if annotation.type == "arrow":
                img = self._draw_arrow(img, annotation, step)
            elif annotation.type == "box":
                img = self._draw_box(img, annotation, step)
            elif annotation.type == "highlight":
                pil_img = self._draw_highlight(pil_img, annotation, step)
            elif annotation.type == "blur":
                pil_img = self._draw_blur(pil_img, annotation, step)
            elif annotation.type == "text":
                pil_img = self._draw_text(pil_img, annotation)
            elif annotation.type == "number":
                img = self._draw_number(img, annotation, step)
            elif annotation.type == "circle":
                img = self._draw_circle(img, annotation, step)
        
        # Convert PIL image back to OpenCV if it was modified
        if any(a.type in ["highlight", "blur", "text"] for a in step.annotations):
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Save annotated image
        output_filename = step.screenshot_path.stem + "_annotated.png"
        output_path = output_dir / output_filename
        cv2.imwrite(str(output_path), img)
        
        step.annotated_screenshot_path = output_path
        return output_path
    
    def _get_element_center(self, step: Step) -> Optional[Tuple[int, int]]:
        """Get center coordinates of element from bounds"""
        if not step.element_bounds:
            return None
        
        x = step.element_bounds['x'] + step.element_bounds['width'] // 2
        y = step.element_bounds['y'] + step.element_bounds['height'] // 2
        return (x, y)
    
    def _draw_arrow(self, img: np.ndarray, annotation: Annotation, step: Step) -> np.ndarray:
        """Draw an arrow pointing to an element"""
        target_pos = self._get_element_center(step)
        if not target_pos:
            return img
        
        color = self.colors_bgr.get(annotation.color, (0, 0, 255))
        
        # Calculate arrow start position (offset from target)
        offset_x, offset_y = -100, -100
        start_pos = (target_pos[0] + offset_x, target_pos[1] + offset_y)
        
        # Draw arrow line
        cv2.arrowedLine(img, start_pos, target_pos, color, annotation.thickness, tipLength=0.3)
        
        # Draw label if provided
        if annotation.label:
            label_pos = (start_pos[0] - 20, start_pos[1] - 10)
            cv2.putText(img, annotation.label, label_pos, cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, color, 2, cv2.LINE_AA)
        
        return img
    
    def _draw_box(self, img: np.ndarray, annotation: Annotation, step: Step) -> np.ndarray:
        """Draw a box around an element

        Coordinates in annotation.region are in LOGICAL PIXELS.
        They're converted to physical pixels based on display_scale.

        Supports two modes:
        1. annotation.region: (x, y, width, height) for coordinate-based box (PyAutoGUI)
        2. step.element_bounds: For element-based box (Appium)
        """
        # Try annotation.region first (for PyAutoGUI)
        if annotation.region:
            x, y, width, height = annotation.region  # Logical pixels from config

            # Convert to physical pixels using display scale
            phys_x = int(x * self.display_scale)
            phys_y = int(y * self.display_scale)
            phys_width = int(width * self.display_scale)
            phys_height = int(height * self.display_scale)

            top_left = (phys_x, phys_y)
            bottom_right = (phys_x + phys_width, phys_y + phys_height)
        # Fall back to element_bounds (for Appium)
        elif step.element_bounds:
            bounds = step.element_bounds
            top_left = (bounds['x'], bounds['y'])
            bottom_right = (bounds['x'] + bounds['width'], bounds['y'] + bounds['height'])
        else:
            print(f"  Warning: Box annotation missing both 'region' and element_bounds in step '{step.name}'")
            return img

        color = self.colors_bgr.get(annotation.color, (255, 0, 0))
        cv2.rectangle(img, top_left, bottom_right, color, annotation.thickness)

        return img
    
    def _draw_highlight(self, img: Image.Image, annotation: Annotation, step: Step) -> Image.Image:
        """Draw a semi-transparent highlight over an element

        Coordinates in annotation.region are in LOGICAL PIXELS.
        They're converted to physical pixels based on display_scale.

        Supports two modes:
        1. annotation.region: (x, y, width, height) for coordinate-based highlight (PyAutoGUI)
        2. step.element_bounds: For element-based highlight (Appium)
        """
        # Try annotation.region first (for PyAutoGUI)
        if annotation.region:
            x, y, width, height = annotation.region  # Logical pixels from config

            # Convert to physical pixels using display scale
            phys_x = int(x * self.display_scale)
            phys_y = int(y * self.display_scale)
            phys_width = int(width * self.display_scale)
            phys_height = int(height * self.display_scale)

            box = [phys_x, phys_y, phys_x + phys_width, phys_y + phys_height]
        # Fall back to element_bounds (for Appium)
        elif step.element_bounds:
            bounds = step.element_bounds
            box = [
                bounds['x'],
                bounds['y'],
                bounds['x'] + bounds['width'],
                bounds['y'] + bounds['height']
            ]
        else:
            print(f"  Warning: Highlight annotation missing both 'region' and element_bounds in step '{step.name}'")
            return img

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        color_rgb = self.colors_rgb.get(annotation.color, (255, 255, 0))
        color_with_alpha = color_rgb + (100,)  # 100 = alpha value

        draw.rectangle(box, fill=color_with_alpha)

        # Composite with original image
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        return img.convert('RGB')
    
    def _draw_blur(self, img: Image.Image, annotation: Annotation, step: Step) -> Image.Image:
        """Apply blur to an element (for sensitive data)

        Coordinates in annotation.region are in LOGICAL PIXELS.
        They're converted to physical pixels based on detected screenshot scale.

        Supports two modes:
        1. annotation.region: (x, y, width, height) for coordinate-based blur (PyAutoGUI)
        2. step.element_bounds: For element-based blur (Appium)
        """
        # Try annotation.region first (for PyAutoGUI)
        if annotation.region:
            x, y, width, height = annotation.region  # Logical pixels from config

            # Convert to physical pixels using display scale
            phys_x = int(x * self.display_scale)
            phys_y = int(y * self.display_scale)
            phys_width = int(width * self.display_scale)
            phys_height = int(height * self.display_scale)

            box = (phys_x, phys_y, phys_x + phys_width, phys_y + phys_height)
        # Fall back to element_bounds (for Appium)
        elif step.element_bounds:
            bounds = step.element_bounds
            box = (
                bounds['x'],
                bounds['y'],
                bounds['x'] + bounds['width'],
                bounds['y'] + bounds['height']
            )
        else:
            print(f"  Warning: Blur annotation missing both 'region' and element_bounds in step '{step.name}'")
            return img

        # Ensure coordinates are within image bounds
        x1, y1, x2, y2 = box
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(img.width, x2)
        y2 = min(img.height, y2)

        if x1 >= x2 or y1 >= y2:
            print(f"  Warning: Blur region {box} out of bounds for image size {img.size}")
            return img

        # Extract region to blur
        box = (x1, y1, x2, y2)
        region = img.crop(box)

        # Apply Gaussian blur
        blurred = region.filter(ImageFilter.GaussianBlur(radius=15))

        # Paste back
        img.paste(blurred, box)

        return img

    def _draw_text(self, img: Image.Image, annotation: Annotation) -> Image.Image:
        """Draw text callout

        Coordinates in annotation.position are in LOGICAL PIXELS.
        They're converted to physical pixels based on display_scale.
        """
        if not annotation.position or not annotation.label:
            return img

        draw = ImageDraw.Draw(img)
        color = self.colors_rgb.get(annotation.color, (0, 0, 0))

        # Draw text with background
        text = annotation.label

        # Convert logical pixels to physical pixels
        x_logical, y_logical = annotation.position
        x_phys = int(x_logical * self.display_scale)
        y_phys = int(y_logical * self.display_scale)
        position = (x_phys, y_phys)
        
        # Get text size (approximate)
        bbox = draw.textbbox(position, text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw background rectangle
        padding = 5
        bg_box = [
            position[0] - padding,
            position[1] - padding,
            position[0] + text_width + padding,
            position[1] + text_height + padding
        ]
        draw.rectangle(bg_box, fill=(255, 255, 255), outline=color, width=2)
        
        # Draw text
        draw.text(position, text, fill=color, font=self.font)
        
        return img
    
    def _draw_number(self, img: np.ndarray, annotation: Annotation, step: Step) -> np.ndarray:
        """Draw a numbered circle on an element"""
        target_pos = self._get_element_center(step)
        if not target_pos:
            return img

        color = self.colors_bgr.get(annotation.color, (255, 0, 0))

        # Draw circle
        radius = 20
        cv2.circle(img, target_pos, radius, color, -1)  # Filled circle
        cv2.circle(img, target_pos, radius, (255, 255, 255), 2)  # White border

        # Draw number
        if annotation.label:
            text = annotation.label
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2

            # Get text size to center it
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = target_pos[0] - text_size[0] // 2
            text_y = target_pos[1] + text_size[1] // 2

            cv2.putText(img, text, (text_x, text_y), font, font_scale,
                       (255, 255, 255), thickness, cv2.LINE_AA)

        return img

    def _draw_circle(self, img: np.ndarray, annotation: Annotation, step: Step) -> np.ndarray:
        """Draw a circle to highlight a click location

        Coordinates in annotation.position are in LOGICAL PIXELS.
        They're converted to physical pixels based on display_scale.
        """
        if not annotation.position:
            return img

        # Convert logical pixels to physical pixels
        x_logical, y_logical = annotation.position
        x_phys = int(x_logical * self.display_scale)
        y_phys = int(y_logical * self.display_scale)
        center = (x_phys, y_phys)

        # Get radius and scale it
        radius = annotation.radius if annotation.radius else 30
        radius_phys = int(radius * self.display_scale)

        color = self.colors_bgr.get(annotation.color, (0, 0, 255))  # Default red
        thickness = annotation.thickness if annotation.thickness else 2
        thickness_phys = int(thickness * self.display_scale)

        # Draw circle outline
        cv2.circle(img, center, radius_phys, color, thickness_phys, cv2.LINE_AA)

        return img
    
    def batch_annotate(self, steps: List[Step], output_dir: Path) -> List[Path]:
        """Annotate all steps in a workflow"""
        output_dir.mkdir(parents=True, exist_ok=True)
        annotated_paths = []
        
        for step in steps:
            path = self.annotate_step(step, output_dir)
            if path:
                annotated_paths.append(path)
                print(f"Annotated: {step.name}")
        
        return annotated_paths
