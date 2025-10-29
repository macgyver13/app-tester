#!/usr/bin/env python3
"""
PyAutoGUI Click Recorder - Records mouse clicks and coordinates
This helps you build automation scripts by recording where you click
"""
import pyautogui
import time
import yaml
from pathlib import Path
from pynput import mouse
from typing import Optional
import threading
import sys

# PyObjC imports for transparent overlay
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode
from AppKit import (
    NSApplication, NSWindow, NSView, NSColor, NSBezierPath,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSNormalWindowLevel, NSApplicationActivationPolicyAccessory,
    NSTextField, NSFont, NSScreen
)
from Cocoa import NSMakeRect


class TransparentOverlayView(NSView):
    """Custom view that draws a red border"""
    
    def drawRect_(self, rect):
        """Draw the overlay content"""
        # Fill with semi-transparent red background
        NSColor.colorWithRed_green_blue_alpha_(1.0, 0.0, 0.0, 0.3).set()
        NSBezierPath.fillRect_(rect)
        
        # Draw thick red border
        border_rect = NSMakeRect(5, 5, rect.size.width - 10, rect.size.height - 10)
        border_path = NSBezierPath.bezierPathWithRect_(border_rect)
        NSColor.redColor().set()
        border_path.setLineWidth_(10.0)
        border_path.stroke()


class CropOverlay:
    """Persistent overlay showing crop region using PyObjC with transparency"""

    def __init__(self, display_scale=1.0):
        self.window = None
        self.view = None
        self.current_crop = None
        self.app = None
        self.labels = []
        self.display_scale = display_scale
        
        # Initialize NSApplication if not already done
        self.app = NSApplication.sharedApplication()
        if not self.app.delegate():
            self.app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    def show(self, crop_region: list):
        """Show or update overlay with crop region [x, y, width, height]"""
        if not crop_region or len(crop_region) != 4:
            self.hide()
            return

        x, y, width, height = crop_region
        self.current_crop = crop_region
        
        # Get the screen that contains this point (x, y)
        # This ensures we use the correct screen in multi-monitor setups
        from AppKit import NSScreen
        target_screen = None
        target_point = NSMakeRect(x, y, 1, 1)
        
        for screen in NSScreen.screens():
            screen_frame = screen.frame()
            # Check if our point is within this screen's bounds
            if (x >= screen_frame.origin.x and 
                x < screen_frame.origin.x + screen_frame.size.width):
                target_screen = screen
                break
        
        # Fallback to main screen if not found
        if target_screen is None:
            target_screen = NSScreen.mainScreen()
        
        screen_frame = target_screen.frame()
        screen_height = screen_frame.size.height
        backing_scale = target_screen.backingScaleFactor()
        
        # macOS NSWindow uses "points" coordinate system, which is what we have
        # No scaling needed - just convert from top-left to bottom-left origin
        cocoa_y = screen_height - y - height
        
        # Close existing window if any
        if self.window:
            self.window.close()
            self.window = None

        # Create the window using point coordinates (no scaling)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, cocoa_y, width, height),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        
        # Configure window for transparency
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setAlphaValue_(1.0)
        self.window.setLevel_(NSNormalWindowLevel)
        self.window.setIgnoresMouseEvents_(True)
        
        # Create custom view for drawing
        self.view = TransparentOverlayView.alloc().initWithFrame_(
            NSMakeRect(0, 0, width, height)
        )
        self.window.setContentView_(self.view)
        
        # Add text labels
        self._add_labels(x, y, width, height)
        
        # Show the window first
        self.window.makeKeyAndOrderFront_(None)
        self.window.orderBack_(None)  # Send to back
        
        # IMPORTANT: Set frame AFTER window is visible to ensure correct positioning
        self.window.setFrame_display_animate_(
            NSMakeRect(x, cocoa_y, width, height),
            True,  # Display immediately
            False  # No animation
        )
        
        # Process events to make window visible
        self._process_events()

    def _add_labels(self, x, y, width, height):
        """Add text labels showing crop region info"""
        # Title label
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, height - 40, 300, 30))
        title_label.setStringValue_("Crop Region")
        title_label.setFont_(NSFont.boldSystemFontOfSize_(20))
        title_label.setTextColor_(NSColor.whiteColor())
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setSelectable_(False)
        self.view.addSubview_(title_label)
        
        # Position label
        pos_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, height - 70, 300, 25))
        pos_label.setStringValue_(f"Position: ({x}, {y})")
        pos_label.setFont_(NSFont.systemFontOfSize_(16))
        pos_label.setTextColor_(NSColor.whiteColor())
        pos_label.setBezeled_(False)
        pos_label.setDrawsBackground_(False)
        pos_label.setEditable_(False)
        pos_label.setSelectable_(False)
        self.view.addSubview_(pos_label)
        
        # Size label
        size_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, height - 95, 300, 25))
        size_label.setStringValue_(f"Size: {width}x{height}")
        size_label.setFont_(NSFont.systemFontOfSize_(16))
        size_label.setTextColor_(NSColor.whiteColor())
        size_label.setBezeled_(False)
        size_label.setDrawsBackground_(False)
        size_label.setEditable_(False)
        size_label.setSelectable_(False)
        self.view.addSubview_(size_label)

    def _process_events(self):
        """Process pending events to update the window"""
        if self.app:
            # Process events to force window to render
            from AppKit import NSEvent, NSAnyEventMask, NSDefaultRunLoopMode
            from Foundation import NSDate
            
            # Process all pending events
            for _ in range(10):  # Process multiple times to ensure rendering
                event = self.app.nextEventMatchingMask_untilDate_inMode_dequeue_(
                    NSAnyEventMask,
                    NSDate.dateWithTimeIntervalSinceNow_(0.01),
                    NSDefaultRunLoopMode,
                    False
                )
                if event:
                    self.app.sendEvent_(event)
                self.app.updateWindows()

    def hide(self):
        """Hide the overlay"""
        if self.window:
            self.window.orderOut_(None)

    def update_crop(self, crop_region: Optional[list]):
        """Update to show new crop region"""
        if crop_region:
            self.show(crop_region)
        else:
            self.hide()

    def destroy(self):
        """Destroy the overlay window"""
        if self.window:
            self.window.close()
            self.window = None
        self.view = None
        self.current_crop = None
        self.display_image = None
        self.current_crop = None


class ConfigEditor:
    """Interactive editor for config.yaml files - add/edit annotations and coordinates"""

    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.config = None
        self.modified = False
        self.load_config()

    def load_config(self):
        """Load config.yaml file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        print(f"✓ Loaded config: {self.config.get('wallet', {}).get('name', 'Unknown')}")

    def save_config(self):
        """Save config back to file"""
        if not self.modified:
            print("No changes to save.")
            return

        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"✓ Saved changes to: {self.config_path}")
        self.modified = False

    def get_sections(self):
        """Get list of section names"""
        doc_config = self.config.get('documentation', {})
        sections = doc_config.get('sections', {})
        return list(sections.keys())

    def get_section(self, section_name):
        """Get section configuration"""
        return self.config.get('documentation', {}).get('sections', {}).get(section_name)

    def get_steps(self, section_name):
        """Get steps for a section"""
        section = self.get_section(section_name)
        if not section:
            return []
        return section.get('steps', [])

    def get_crop_region(self, section_name):
        """Get crop region for a section"""
        section = self.get_section(section_name)
        if not section:
            return None
        return section.get('crop')

    def add_annotation_to_step(self, section_name, step_index, annotation):
        """Add annotation to a step"""
        steps = self.get_steps(section_name)
        if step_index < 0 or step_index >= len(steps):
            print(f"Invalid step index: {step_index}")
            return

        step = steps[step_index]
        if 'annotations' not in step:
            step['annotations'] = []

        step['annotations'].append(annotation)
        self.modified = True

    def set_annotations_for_step(self, section_name, step_index, annotations):
        """Replace all annotations for a step"""
        steps = self.get_steps(section_name)
        if step_index < 0 or step_index >= len(steps):
            print(f"Invalid step index: {step_index}")
            return

        step = steps[step_index]
        step['annotations'] = annotations
        self.modified = True

    def add_coordinate(self, section_name, coord_name, position):
        """Add a named coordinate to a section"""
        section = self.get_section(section_name)
        if not section:
            print(f"Section not found: {section_name}")
            return

        if 'coordinates' not in section:
            section['coordinates'] = {}

        section['coordinates'][coord_name] = list(position)
        self.modified = True

    def set_crop_region(self, section_name, crop_region):
        """Set crop region for a section"""
        section = self.get_section(section_name)
        if not section:
            print(f"Section not found: {section_name}")
            return

        section['crop'] = list(crop_region)
        self.modified = True

    def add_step(self, section_name, step, position=None):
        """Add a new step to a section

        Args:
            section_name: Name of the section
            step: Step dictionary to add
            position: Insert position (0-based index, None = append to end)
        """
        section = self.get_section(section_name)
        if not section:
            print(f"Section not found: {section_name}")
            return

        if 'steps' not in section:
            section['steps'] = []

        if position is None:
            section['steps'].append(step)
        else:
            section['steps'].insert(position, step)

        self.modified = True

    def update_step_coordinate(self, section_name, coordinate_name, position):
        """Update the coordinate referenced by a step"""
        section = self.get_section(section_name)
        if not section:
            print(f"Section not found: {section_name}")
            return

        # Update the coordinate in the coordinates dict
        if 'coordinates' not in section:
            section['coordinates'] = {}

        section['coordinates'][coordinate_name] = list(position)
        self.modified = True


class InteractiveConfigEditor:
    """Interactive mode for editing config with mouse clicks"""

    def __init__(self, config_path, display_scale=None, show_overlay=False):
        self.editor = ConfigEditor(config_path)
        self.listener = None
        self.mode = None  # 'blur', 'coordinate', 'crop'
        self.current_section = None
        self.current_step_index = None
        self.capture_buffer = []  # For multi-click captures (blur corners, crop corners)
        self.waiting_for_input = False
        self.show_overlay = show_overlay

        # Read display_scale from config, or use CLI override, default 1.0
        config_scale = self.editor.config.get('automation', {}).get('display_scale', 1.0)
        self.display_scale = display_scale if display_scale else config_scale
        
        # Create overlay with display scale
        self.crop_overlay = CropOverlay(display_scale=self.display_scale) if show_overlay else None
        
        print(f"Using display scale: {self.display_scale}")
        if not show_overlay:
            print("Overlay display: DISABLED")

    def quit_app(self):
        """Exit the application with save prompt if needed"""
        if self.editor.modified:
            save = input("\nYou have unsaved changes. Save before quitting? (y/n): ").strip().lower()
            if save == 'y':
                self.editor.save_config()
                print("✓ Changes saved")

        # Clean up overlay before exiting
        if self.crop_overlay:
            self.crop_overlay.destroy()

        print("\nGoodbye!")
        sys.exit(0)

    def start(self):
        """Start interactive editing session"""
        print("\n" + "="*70)
        print("Interactive Config Editor")
        print("="*70)

        try:
            while True:
                choice = self.show_main_menu()
                if choice == 'q':
                    self.quit_app()
                elif choice == 's':
                    self.editor.save_config()
                elif choice.isdigit():
                    section_idx = int(choice) - 1
                    sections = self.editor.get_sections()
                    if 0 <= section_idx < len(sections):
                        self.current_section = sections[section_idx]
                        self.section_menu()
        finally:
            # Clean up overlay
            if self.crop_overlay:
                self.crop_overlay.destroy()

        print("\n✓ Done!")

    def show_main_menu(self):
        """Show main menu and get user choice"""
        print("\n" + "="*70)
        print("Main Menu")
        print("="*70)

        sections = self.editor.get_sections()
        for i, section in enumerate(sections, 1):
            print(f"  {i}. {section}")

        print("\nOptions:")
        print("  s - Save changes")
        print("  q - Quit")

        return input("\nChoice: ").strip().lower()

    def section_menu(self):
        """Menu for section-level actions"""
        # Show crop overlay for this section
        if self.crop_overlay:
            crop_region = self.editor.get_crop_region(self.current_section)
            if crop_region:
                self.crop_overlay.show(crop_region)
            else:
                self.crop_overlay.hide()

        while True:
            print(f"\n" + "="*70)
            print(f"Section: {self.current_section}")
            print("="*70)

            steps = self.editor.get_steps(self.current_section)
            print("\nSteps:")
            for i, step in enumerate(steps, 1):
                name = step.get('name', f'Step {i}')
                has_screenshot = '📸' if step.get('screenshot') else '  '
                has_annotations = f"({len(step.get('annotations', []))} annotations)" if step.get('annotations') else ''
                print(f"  {i}. {has_screenshot} {name} {has_annotations}")

            print("\nOptions:")
            print("  n - Add new step")
            print("  c - Add/edit section coordinates")
            print("  r - Set crop region")
            print("  s - Save changes")
            print("  b - Back to main menu")
            print("  q - Quit app")

            choice = input("\nChoice (number for step, or option): ").strip().lower()

            if choice == 'b':
                break
            elif choice == 'q':
                self.quit_app()
                return
            elif choice == 's':
                self.editor.save_config()
            elif choice == 'n':
                self.add_new_step()
            elif choice == 'c':
                self.record_coordinates()
            elif choice == 'r':
                self.record_crop_region()
            elif choice.isdigit():
                step_idx = int(choice) - 1
                if 0 <= step_idx < len(steps):
                    self.current_step_index = step_idx
                    self.step_menu()

    def step_menu(self):
        """Menu for step-level actions"""
        steps = self.editor.get_steps(self.current_section)
        step = steps[self.current_step_index]
        step_name = step.get('name', f'Step {self.current_step_index + 1}')

        while True:
            print(f"\n" + "="*70)
            print(f"Step: {step_name}")
            print("="*70)

            # Show current annotations
            annotations = step.get('annotations', [])
            if annotations:
                print("\nCurrent annotations:")
                for i, ann in enumerate(annotations, 1):
                    ann_type = ann.get('type', 'unknown')
                    region = ann.get('region', '')
                    print(f"  {i}. {ann_type}: {region}")
            else:
                print("\nNo annotations yet")

            print("\nOptions:")
            print("  e - Edit step click coordinate")
            print("\nAnnotations:")
            print("  a - Add blur annotation")
            print("  h - Add highlight annotation")
            print("  x - Add box annotation")
            print("  t - Add text annotation")
            print("  c - Add circle annotation")
            print("  r - Replace all annotations (clear and add new)")
            print("\nMenu:")
            print("  s - Save changes")
            print("  b - Back to section menu")
            print("  q - Quit app")

            choice = input("\nChoice: ").strip().lower()

            if choice == 'b':
                break
            elif choice == 'q':
                self.quit_app()
                return
            elif choice == 's':
                self.editor.save_config()
            elif choice == 'e':
                self.edit_step_coordinate()
            elif choice == 'a':
                self.record_blur_annotation(append=True)
            elif choice == 'h':
                self.record_region_annotation('highlight', append=True)
            elif choice == 'x':
                self.record_region_annotation('box', append=True)
            elif choice == 't':
                self.record_point_annotation('text', append=True)
            elif choice == 'c':
                self.record_point_annotation('circle', append=True)
            elif choice == 'r':
                # Ask which type to replace with
                print("\nReplace all annotations with:")
                print("  1 - Blur")
                print("  2 - Highlight")
                print("  3 - Box")
                print("  4 - Text")
                print("  5 - Circle")
                replace_choice = input("Choice: ").strip()
                if replace_choice == '1':
                    self.record_blur_annotation(append=False)
                elif replace_choice == '2':
                    self.record_region_annotation('highlight', append=False)
                elif replace_choice == '3':
                    self.record_region_annotation('box', append=False)
                elif replace_choice == '4':
                    self.record_point_annotation('text', append=False)
                elif replace_choice == '5':
                    self.record_point_annotation('circle', append=False)
                else:
                    print("✗ Invalid choice")

    def edit_step_coordinate(self):
        """Edit the click coordinate for current step"""
        steps = self.editor.get_steps(self.current_section)
        step = steps[self.current_step_index]

        # Get the target coordinate name
        target = step.get('target')
        if not target:
            print("\n✗ Step has no target coordinate")
            return

        print("\n" + "="*70)
        print(f"Edit Coordinate: {target}")
        print("="*70)
        print("Click on the new target location...")

        self.mode = 'edit_coord'
        self.capture_buffer = []

        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click_for_edit_coord)
        self.listener.start()

        # Wait for 1 click
        while self.listener.is_alive():
            time.sleep(0.1)

        if len(self.capture_buffer) >= 1:
            x, y = self.capture_buffer[0]

            # Update the coordinate
            self.editor.update_step_coordinate(self.current_section, target, (x, y))

            print(f"\n✓ Coordinate '{target}' updated to: ({x}, {y})")
        else:
            print("\n✗ No click recorded")

        self.mode = None
        self.capture_buffer = []

    def record_region_annotation(self, annotation_type, append=True):
        """Record region-based annotation (blur, highlight, box) - 2 click workflow

        Args:
            annotation_type: 'blur', 'highlight', or 'box'
            append: If True, add to existing annotations. If False, replace all.
        """
        type_names = {
            'blur': 'Blur',
            'highlight': 'Highlight',
            'box': 'Box'
        }

        print("\n" + "="*70)
        print(f"Recording {type_names.get(annotation_type, annotation_type.title())} Annotation")
        print("="*70)
        print("Click upper-left corner, then lower-right corner of the region.\n")

        crop_region = self.editor.get_crop_region(self.current_section)
        if not crop_region:
            print("Warning: No crop region defined for this section.")
            print("Coordinates will be relative to full screen.")
            crop_x, crop_y = 0, 0
        else:
            crop_x, crop_y = crop_region[0], crop_region[1]
            print(f"Crop region (logical): {crop_region}")
            print(f"Display scale: {self.display_scale}x\n")

        self.mode = 'region_annotation'
        self.capture_buffer = []

        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click_for_region_annotation)
        self.listener.start()

        # Wait for 2 clicks (listener will stop itself after 2 clicks)
        while self.listener.is_alive():
            time.sleep(0.1)

        # Process the captured region
        if len(self.capture_buffer) >= 2:
            x1, y1 = self.capture_buffer[0]
            x2, y2 = self.capture_buffer[1]

            # Calculate region relative to crop (all in logical pixels)
            rel_x = min(x1, x2) - crop_x
            rel_y = min(y1, y2) - crop_y
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            region = [int(rel_x), int(rel_y), int(width), int(height)]
            annotation = {'type': annotation_type, 'region': region}

            print(f"\n✓ {type_names.get(annotation_type, annotation_type.title())} region: {region}")

            if append:
                self.editor.add_annotation_to_step(
                    self.current_section,
                    self.current_step_index,
                    annotation
                )
                print(f"✓ {type_names.get(annotation_type, annotation_type.title())} annotation added")
            else:
                self.editor.set_annotations_for_step(
                    self.current_section,
                    self.current_step_index,
                    [annotation]
                )
                print(f"✓ Annotations replaced with this {annotation_type} region")
        else:
            print("\n✗ Capture cancelled (need 2 clicks)")

        self.mode = None
        self.capture_buffer = []

    def record_blur_annotation(self, append=True):
        """Record blur annotation region (single region per call)"""
        self.record_region_annotation('blur', append)

    def record_point_annotation(self, annotation_type, append=True):
        """Record point-based annotation (text, circle) - 1 click workflow

        Args:
            annotation_type: 'text' or 'circle'
            append: If True, add to existing annotations. If False, replace all.
        """
        type_names = {
            'text': 'Text',
            'circle': 'Circle'
        }

        print("\n" + "="*70)
        print(f"Recording {type_names.get(annotation_type, annotation_type.title())} Annotation")
        print("="*70)
        print("Click on the target position.\n")

        crop_region = self.editor.get_crop_region(self.current_section)
        if not crop_region:
            print("Warning: No crop region defined for this section.")
            print("Coordinates will be relative to full screen.")
            crop_x, crop_y = 0, 0
        else:
            crop_x, crop_y = crop_region[0], crop_region[1]
            print(f"Crop region (logical): {crop_region}")
            print(f"Display scale: {self.display_scale}x\n")

        self.mode = 'point_annotation'
        self.capture_buffer = []

        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click_for_point_annotation)
        self.listener.start()

        # Wait for 1 click
        while self.listener.is_alive():
            time.sleep(0.1)

        # Process the captured point
        if len(self.capture_buffer) >= 1:
            x, y = self.capture_buffer[0]

            # Calculate position relative to crop (all in logical pixels)
            rel_x = x - crop_x
            rel_y = y - crop_y

            position = [int(rel_x), int(rel_y)]

            # Build annotation based on type
            if annotation_type == 'text':
                text = input("\nEnter text label: ").strip()
                if not text:
                    print("✗ Text label required")
                    self.mode = None
                    self.capture_buffer = []
                    return
                annotation = {'type': 'text', 'position': position, 'label': text}
                print(f"✓ Text annotation: '{text}' at {position}")

            elif annotation_type == 'circle':
                radius_input = input("\nEnter circle radius (or press Enter for default 30): ").strip()
                if radius_input:
                    try:
                        radius = int(radius_input)
                    except ValueError:
                        print("✗ Invalid radius, using default 30")
                        radius = 30
                else:
                    radius = 30
                annotation = {'type': 'circle', 'position': position, 'radius': radius}
                print(f"✓ Circle annotation: radius {radius} at {position}")

            else:
                print(f"✗ Unknown annotation type: {annotation_type}")
                self.mode = None
                self.capture_buffer = []
                return

            if append:
                self.editor.add_annotation_to_step(
                    self.current_section,
                    self.current_step_index,
                    annotation
                )
                print(f"✓ {type_names.get(annotation_type, annotation_type.title())} annotation added")
            else:
                self.editor.set_annotations_for_step(
                    self.current_section,
                    self.current_step_index,
                    [annotation]
                )
                print(f"✓ Annotations replaced with this {annotation_type} annotation")
        else:
            print("\n✗ Capture cancelled (need 1 click)")

        self.mode = None
        self.capture_buffer = []

    def add_new_step(self):
        """Add a new step with click action"""
        print("\n" + "="*70)
        print("Add New Step")
        print("="*70)

        # Prompt for step name
        step_name = input("Enter step name: ").strip()
        if not step_name:
            print("✗ Step name required")
            return

        # Prompt for description (optional)
        description = input("Enter step description (optional): ").strip()
        if not description:
            description = f"Click on {step_name}"

        # Ask where to insert
        steps = self.editor.get_steps(self.current_section)
        print(f"\nCurrent steps: {len(steps)}")
        position_input = input(f"Insert at position (1-{len(steps) + 1}, or Enter for end): ").strip()

        if position_input:
            try:
                position = int(position_input) - 1  # Convert to 0-based
                if position < 0 or position > len(steps):
                    print(f"✗ Invalid position. Must be 1-{len(steps) + 1}")
                    return
            except ValueError:
                print("✗ Invalid position")
                return
        else:
            position = None  # Append to end

        # Record click position
        print("\nClick on the target location...")
        self.mode = 'new_step'
        self.capture_buffer = []

        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click_for_new_step)
        self.listener.start()

        # Wait for 1 click
        while self.listener.is_alive():
            time.sleep(0.1)

        if len(self.capture_buffer) >= 1:
            x, y = self.capture_buffer[0]

            # Create coordinate name from step name
            coord_name = step_name.lower().replace(' ', '_')

            # Add coordinate to section
            self.editor.add_coordinate(self.current_section, coord_name, (x, y))

            # Create step
            step = {
                'name': step_name,
                'description': description,
                'action': 'click',
                'target': coord_name,
                'screenshot': True
            }

            # Add step at position
            self.editor.add_step(self.current_section, step, position)

            print(f"\n✓ Step '{step_name}' added at position {position + 1 if position is not None else len(steps) + 1}")
            print(f"✓ Coordinate '{coord_name}': ({x}, {y})")
        else:
            print("\n✗ No click recorded")

        self.mode = None
        self.capture_buffer = []

    def record_coordinates(self):
        """Record named coordinates for section"""
        print("\n" + "="*70)
        print("Recording Section Coordinates")
        print("="*70)
        print("Click on UI elements to capture coordinates.")
        print("You'll be prompted to name each coordinate.")
        print("Press Ctrl+C when done.\n")

        self.mode = 'coordinate'
        self.capture_buffer = []

        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click_for_coordinate)
        self.listener.start()

        try:
            while True:
                if not self.waiting_for_input:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n✓ Recording stopped")

        if self.listener:
            self.listener.stop()

        self.mode = None
        self.capture_buffer = []

    def record_crop_region(self):
        """Record crop region for section"""
        print("\n" + "="*70)
        print("Recording Crop Region")
        print("="*70)
        print("Click upper-left corner, then lower-right corner of crop area.\n")

        self.mode = 'crop'
        self.capture_buffer = []

        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click_for_crop)
        self.listener.start()

        try:
            while True:
                time.sleep(0.1)
                if len(self.capture_buffer) >= 2:
                    break
        except KeyboardInterrupt:
            print("\n✓ Recording cancelled")

        if self.listener:
            self.listener.stop()

        if len(self.capture_buffer) >= 2:
            x1, y1 = self.capture_buffer[0]
            x2, y2 = self.capture_buffer[1]

            crop_x = min(x1, x2)
            crop_y = min(y1, y2)
            crop_width = abs(x2 - x1)
            crop_height = abs(y2 - y1)

            crop_region = [crop_x, crop_y, crop_width, crop_height]
            self.editor.set_crop_region(self.current_section, crop_region)
            print(f"\n✓ Crop region set: {crop_region}")

            # Update the overlay to show new crop region
            if self.crop_overlay:
                self.crop_overlay.show(crop_region)

        self.mode = None
        self.capture_buffer = []

    def on_click_for_region_annotation(self, x, y, button, pressed):
        """Handle mouse clicks for region annotation recording (blur/highlight/box)"""
        if pressed and button == mouse.Button.left:
            # pynput reports logical pixels (same as PyAutoGUI coordinate system)
            self.capture_buffer.append((x, y))
            count = len(self.capture_buffer)

            if count == 1:
                print(f"✓ Upper-left corner: ({x}, {y})")
                print("  Click lower-right corner...")
            elif count == 2:
                print(f"✓ Lower-right corner: ({x}, {y})")
                # Stop listener after 2 clicks
                if self.listener:
                    self.listener.stop()

    def on_click_for_point_annotation(self, x, y, button, pressed):
        """Handle mouse click for point annotation recording (text/circle)"""
        if pressed and button == mouse.Button.left:
            # pynput reports logical pixels (same as PyAutoGUI coordinate system)
            self.capture_buffer.append((x, y))
            print(f"✓ Position recorded: ({x}, {y})")
            # Stop listener after 1 click
            if self.listener:
                self.listener.stop()

    def on_click_for_coordinate(self, x, y, button, pressed):
        """Handle mouse clicks for coordinate recording"""
        if pressed and button == mouse.Button.left:
            self.waiting_for_input = True
            self.listener.stop()

            # pynput reports logical pixels (same as PyAutoGUI coordinate system)
            # No conversion needed - use coordinates directly
            print(f"\n✓ Position: ({x}, {y})")
            name = input("  Enter coordinate name (or press Enter to skip): ").strip()

            if name:
                self.editor.add_coordinate(self.current_section, name, (x, y))
                print(f"  ✓ Saved coordinate '{name}': ({x}, {y})")

            # Resume listener
            self.waiting_for_input = False
            self.listener = mouse.Listener(on_click=self.on_click_for_coordinate)
            self.listener.start()

    def on_click_for_crop(self, x, y, button, pressed):
        """Handle mouse clicks for crop region recording"""
        if pressed and button == mouse.Button.left:
            # pynput reports logical pixels (same as PyAutoGUI coordinate system)
            # No conversion needed - use coordinates directly
            self.capture_buffer.append((x, y))
            count = len(self.capture_buffer)

            if count == 1:
                print(f"✓ Upper-left: ({x}, {y}) [pynput raw] - Click lower-right corner...")
            elif count == 2:
                print(f"✓ Lower-right: ({x}, {y}) [pynput raw]")
                # Debug: show what will be saved
                x1, y1 = self.capture_buffer[0]
                x2, y2 = self.capture_buffer[1]
                crop_x = min(x1, x2)
                crop_y = min(y1, y2)
                crop_width = abs(x2 - x1)
                crop_height = abs(y2 - y1)
                print(f"  DEBUG: Will save crop as: [{crop_x}, {crop_y}, {crop_width}, {crop_height}]")

    def on_click_for_new_step(self, x, y, button, pressed):
        """Handle mouse click for new step coordinate"""
        if pressed and button == mouse.Button.left:
            # pynput reports logical pixels (same as PyAutoGUI coordinate system)
            self.capture_buffer.append((x, y))
            print(f"✓ Position recorded: ({x}, {y})")
            # Stop listener after 1 click
            if self.listener:
                self.listener.stop()

    def on_click_for_edit_coord(self, x, y, button, pressed):
        """Handle mouse click for editing step coordinate"""
        if pressed and button == mouse.Button.left:
            # pynput reports logical pixels (same as PyAutoGUI coordinate system)
            self.capture_buffer.append((x, y))
            print(f"✓ New position recorded: ({x}, {y})")
            # Stop listener after 1 click
            if self.listener:
                self.listener.stop()


class ClickRecorder:
    def __init__(self, setup_crop=False, crop=None, interactive=False):
        self.clicks = []
        self.start_time = time.time()
        self.setup_crop = setup_crop
        self.interactive = interactive
        self.crop_region = None
        self.crop_corner1 = None
        self.crop_corner2 = None
        self.listener = None
        self.waiting_for_name = False
        
        # If crop provided directly, parse it
        if crop:
            try:
                x, y, width, height = map(int, crop.split(','))
                self.crop_region = (x, y, width, height)
                print(f"Using provided crop region: {self.crop_region}")
            except:
                print(f"Warning: Invalid crop format '{crop}', expected 'x,y,width,height'")
        
    def on_click(self, x, y, button, pressed):
        """Called when mouse button is pressed"""
        if pressed and button == mouse.Button.left:
            # Handle crop setup mode
            if self.setup_crop and self.crop_region is None:
                if self.crop_corner1 is None:
                    self.crop_corner1 = (x, y)
                    print(f"\n✓ Upper-left corner recorded: ({x}, {y})")
                    print("Now click the lower-right corner of the crop region...")
                    return
                elif self.crop_corner2 is None:
                    self.crop_corner2 = (x, y)
                    # Calculate crop region
                    x1, y1 = self.crop_corner1
                    x2, y2 = self.crop_corner2
                    crop_x = min(x1, x2)
                    crop_y = min(y1, y2)
                    crop_width = abs(x2 - x1)
                    crop_height = abs(y2 - y1)
                    self.crop_region = (crop_x, crop_y, crop_width, crop_height)
                    print(f"✓ Lower-right corner recorded: ({x}, {y})")
                    print(f"\n✓ Crop region set: {self.crop_region}")
                    print(f"  Position: ({crop_x}, {crop_y})")
                    print(f"  Size: {crop_width}x{crop_height}")
                    print("\nNow recording regular clicks...\n")
                    return
            
            # Regular click recording
            elapsed = time.time() - self.start_time
            click_data = {
                'x': int(x),
                'y': int(y),
                'time': elapsed,
                'step': len(self.clicks) + 1,
                'name': None
            }
            
            print(f"\n✓ Click {len(self.clicks) + 1}: Position ({x}, {y})")
            
            # If interactive mode, pause listener and prompt for name
            if self.interactive:
                self.waiting_for_name = True
                self.listener.stop()
                
                # Prompt for name
                name = input("  Enter name for this coordinate (or press Enter to skip): ").strip()
                if name:
                    click_data['name'] = name
                    print(f"  Saved as: {name}")
                else:
                    click_data['name'] = f"coord_{len(self.clicks) + 1}"
                    print(f"  Auto-named: {click_data['name']}")
                
                self.clicks.append(click_data)
                
                # Resume listener
                self.waiting_for_name = False
                self.listener = mouse.Listener(on_click=self.on_click)
                self.listener.start()
            else:
                self.clicks.append(click_data)
                print(f"  Add to script: target=\"{x},{y}\"")
    
    def start_recording(self):
        """Start recording clicks for specified duration"""
        print("="*70)
        print("PyAutoGUI Click Recorder")
        print("="*70)
        
        if self.setup_crop and self.crop_region is None:
            print("\nSETUP MODE: Define crop region first")
            print("1. Click the UPPER-LEFT corner of the area to capture")
            print("2. Click the LOWER-RIGHT corner of the area to capture")
            print("3. Then record normal clicks\n")
        elif self.crop_region:
            print(f"\nUsing crop region: {self.crop_region}\n")
        else:
            print("\nClick on UI elements in your app to record their positions.")
        
        if self.interactive:
            print("INTERACTIVE MODE: You'll be prompted to name each coordinate.\n")
        
        print("Press Ctrl+C to stop.\n")
        
        # Start mouse listener
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        
        try:
            while True:
                if not self.waiting_for_name:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n✓ Recording stopped")
        
        if self.listener:
            self.listener.stop()
        self.generate_code()
    
    def generate_code(self):
        """Generate config.yaml format from recorded clicks"""
        if not self.clicks:
            print("\n✗ No clicks recorded")
            return

        print("\n\n" + "="*70)
        print(f"Recorded {len(self.clicks)} clicks")
        print("="*70)

        # Show crop region if set
        if self.crop_region:
            crop_x, crop_y, crop_width, crop_height = self.crop_region
            print(f"\nCrop Region: {self.crop_region}")
            print(f"  Position: ({crop_x}, {crop_y})")
            print(f"  Size: {crop_width}x{crop_height}")

        # Show summary
        print("\nClick Summary:")
        for click in self.clicks:
            if click.get('name'):
                print(f"  {click['name']}: ({click['x']}, {click['y']}) at {click['time']:.1f}s")
            else:
                print(f"  Step {click['step']}: ({click['x']}, {click['y']}) at {click['time']:.1f}s")

        # Generate config.yaml format
        print("\n" + "="*70)
        print("Generated config.yaml section (copy/paste into your config):")
        print("="*70)
        print()

        print("  sections:")
        print("    your_section_name:")
        print("      title: \"Your Section Title\"")
        print("      description: \"Description of this section\"")

        # Add crop region
        if self.crop_region:
            crop_x, crop_y, crop_width, crop_height = self.crop_region
            print(f"      crop: [{crop_x}, {crop_y}, {crop_width}, {crop_height}]")
        else:
            print("      crop: [100, 100, 1200, 800]  # Adjust as needed")

        # Add coordinates if interactive mode
        if self.interactive and any(click.get('name') for click in self.clicks):
            print("      coordinates:")
            for click in self.clicks:
                if click.get('name'):
                    print(f"        {click['name']}: [{click['x']}, {click['y']}]")

            print("      steps:")
            # Generate steps using named coordinates
            for click in self.clicks:
                if click.get('name'):
                    step_name = click['name'].replace('_', ' ').title()
                    print(f"        - name: \"{step_name}\"")
                    print(f"          description: \"TODO: Describe what this does\"")
                    print(f"          action: \"click\"")
                    print(f"          target: \"{click['name']}\"")
                    print(f"          screenshot: true")
                    print()
        else:
            # Generate coordinates with auto-names
            print("      coordinates:")
            for i, click in enumerate(self.clicks, 1):
                coord_name = f"coord_{i}"
                print(f"        {coord_name}: [{click['x']}, {click['y']}]")

            print("      steps:")
            # Generate steps with auto-named coordinates
            for i, click in enumerate(self.clicks, 1):
                coord_name = f"coord_{i}"
                print(f"        - name: \"Step {i}\"")
                print(f"          description: \"TODO: Describe what this does\"")
                print(f"          action: \"click\"")
                print(f"          target: \"{coord_name}\"")
                print(f"          screenshot: true")
                print()

        print("\n" + "="*70)
        print("Usage Tips:")
        print("="*70)
        print("1. Copy the section above to your config.yaml")
        print("2. Replace 'your_section_name' with a meaningful name (e.g., 'setup', 'usage')")
        print("3. Update the title and description")
        print("4. Fill in step descriptions (replace TODO comments)")
        print("5. Adjust action types if needed (click, type, wait, screenshot)")
        print("6. Add more properties: notes, flags, omit_from_output, etc.")
        print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Record mouse clicks and generate automation code")
    parser.add_argument('--setup-crop', action='store_true',
                        help='First 2 clicks define crop region (upper-left then lower-right)')
    parser.add_argument('--crop', type=str,
                        help='Crop region as "x,y,width,height" (e.g., "100,100,800,600")')
    parser.add_argument('--interactive', action='store_true',
                        help='Prompt for coordinate names after each click')
    parser.add_argument('--edit-config', type=str, metavar='PATH',
                        help='Interactive mode: edit existing config.yaml to add/edit annotations and coordinates')
    parser.add_argument('--display-scale', type=float, default=None,
                        help='Display scale factor (overrides config, typically 2.0 for retina, 1.0 for non-retina)')
    parser.add_argument('--show-overlay', action='store_true', default=False,
                        help='Show red overlay window with crop region info (requires working OpenCV)')
    args = parser.parse_args()

    # Check if edit-config mode
    if args.edit_config:
        try:
            editor = InteractiveConfigEditor(args.edit_config, 
                                            display_scale=args.display_scale,
                                            show_overlay=args.show_overlay)
            editor.start()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        recorder = ClickRecorder(setup_crop=args.setup_crop, crop=args.crop, interactive=args.interactive)
        recorder.start_recording()
