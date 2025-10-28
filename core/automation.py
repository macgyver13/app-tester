"""
Multi-backend automation framework for wallet interaction and screenshot capture

Provides:
- BaseAutomation: Abstract base class for all automation backends
- AppiumAutomation: Appium-based automation (formerly WalletAutomation)
- PyAutoGUIAutomation: PyAutoGUI-based coordinate automation
- create_automation(): Factory function for easy instantiation
"""

import time
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

from appium import webdriver
from appium.options.mac import Mac2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import WalletConfig


@dataclass
class Annotation:
    """Visual annotation for screenshots"""
    
    type: Literal["arrow", "box", "highlight", "blur", "text", "number"]
    target: Optional[str] = None  # Element selector or coordinates
    position: Optional[tuple] = None  # (x, y) coordinates
    label: Optional[str] = None
    color: str = "red"
    thickness: int = 2
    size: Optional[tuple] = None  # For boxes: (width, height)
    
    @classmethod
    def arrow(cls, target: str, label: Optional[str] = None, color: str = "red") -> "Annotation":
        """Create an arrow annotation"""
        return cls(type="arrow", target=target, label=label, color=color)
    
    @classmethod
    def box(cls, target: str, color: str = "blue", thickness: int = 3) -> "Annotation":
        """Create a box annotation"""
        return cls(type="box", target=target, color=color, thickness=thickness)
    
    @classmethod
    def highlight(cls, target: str, color: str = "yellow") -> "Annotation":
        """Create a highlight annotation"""
        return cls(type="highlight", target=target, color=color)
    
    @classmethod
    def blur(cls, target: str) -> "Annotation":
        """Create a blur annotation for sensitive data"""
        return cls(type="blur", target=target)
    
    @classmethod
    def text(cls, text: str, position: tuple, color: str = "black") -> "Annotation":
        """Create a text callout annotation"""
        return cls(type="text", label=text, position=position, color=color)
    
    @classmethod
    def number(cls, number: int, target: str, color: str = "blue") -> "Annotation":
        """Create a numbered step annotation"""
        return cls(type="number", label=str(number), target=target, color=color)


@dataclass
class Step:
    """A single step in the automation workflow"""

    name: str
    description: str
    action: Literal["launch", "click", "type", "wait", "screenshot", "custom"]
    target: Optional[tuple] = None  # Element selector
    clicks: int = 1
    value: Optional[str] = None  # For type actions
    screenshot: bool = False
    crop_to_window: bool = False  # Crop screenshot to app window only
    crop_region: Optional[tuple] = None  # Manual crop: (x, y, width, height)
    annotations: List[Annotation] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)  # ["NEW", "CHANGED", "DEPRECATED"]
    wait_before: float = 0.5  # Seconds to wait before action
    wait_after: float = 0.5  # Seconds to wait after action
    notes: str = ""
    section: Optional[str] = None  # Section grouping (e.g., "setup", "usage", "testing")
    omit_from_output: bool = False  # Skip this step in documentation output

    # Metadata
    step_number: Optional[int] = None
    screenshot_path: Optional[Path] = None
    annotated_screenshot_path: Optional[Path] = None
    timestamp: Optional[str] = None
    element_bounds: Optional[Dict[str, int]] = None  # {"x": 0, "y": 0, "width": 100, "height": 50}
    window_bounds: Optional[Dict[str, int]] = None  # App window bounds for cropping


class BaseAutomation(ABC):
    """Abstract base class for all automation backends

    Provides common interface and shared functionality for different automation approaches.
    Subclasses must implement: connect(), disconnect(), _execute_step(), _capture_screenshot()
    """

    def __init__(
        self,
        name: str,
        app_path: str,
        version: str = "1.0.0",
        config: Optional[WalletConfig] = None
    ):
        self.name = name
        self.app_path = app_path
        self.version = version
        self.config = config or WalletConfig(name=name)
        self.steps: List[Step] = []
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.last_run_sections: Optional[List[str]] = None

        # Setup output directories
        self.config.ensure_directories()

    def add_step(self, step: Step) -> "BaseAutomation":
        """Add a step to the automation workflow"""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)
        return self

    def add_steps_from_config(self, section_name: Optional[str] = None) -> "BaseAutomation":
        """
        Load and add steps from the config file.

        Args:
            section_name: Specific section to load (None = load all sections)

        Returns:
            self for method chaining
        """
        if section_name:
            step_dicts = self.config.get_section_steps(section_name)
        else:
            step_dicts = self.config.get_all_steps()

        for step_dict in step_dicts:
            # Convert dict to Step object
            # Handle list to tuple conversions
            if 'crop_region' in step_dict and isinstance(step_dict['crop_region'], list):
                step_dict['crop_region'] = tuple(step_dict['crop_region'])
            if 'target' in step_dict and isinstance(step_dict['target'], list):
                step_dict['target'] = tuple(step_dict['target'])

            step = Step(**step_dict)
            self.add_step(step)

        return self

    @abstractmethod
    def connect(self):
        """Initialize connection to the application (implementation-specific)"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection and cleanup (implementation-specific)"""
        pass

    @abstractmethod
    def _execute_step(self, step: Step, screenshots_dir: Path):
        """Execute a single automation step (implementation-specific)"""
        pass

    @abstractmethod
    def _capture_screenshot(self, step: Step, screenshots_dir: Path):
        """Capture screenshot for a step (implementation-specific)"""
        pass

    def _sanitize_filename(self, name: str) -> str:
        """Convert step name to valid filename"""
        return name.lower().replace(" ", "_").replace("/", "_")[:50]

    def run(self, staging: bool = True, sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the complete automation workflow

        Args:
            staging: Output to staging area (default: True)
            sections: List of section names to run (default: None = run all)
        """
        # Store which sections were run for later filtering
        self.last_run_sections = sections

        print(f"\n{'='*60}")
        print(f"Starting automation: {self.name} v{self.version}")
        print(f"Session ID: {self.session_id}")
        print(f"Steps: {len(self.steps)}")
        print(f"Mode: {'Staging' if staging else 'Production'}")
        if sections:
            print(f"Sections: {', '.join(sections)}")
        print(f"{'='*60}")

        # Filter steps by section if specified
        steps_to_run = self.steps
        if sections:
            steps_to_run = [s for s in self.steps if s.section in sections]
            print(f"Filtered to {len(steps_to_run)} steps in specified sections")

        # Set screenshot directory based on staging mode
        if staging:
            screenshots_dir = self.config.staging_dir / "screenshots"
        else:
            screenshots_dir = self.config.screenshots_dir

        screenshots_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Connect to app
            self.connect()

            # Execute each step
            for step in steps_to_run:
                try:
                    self._execute_step(step, screenshots_dir)
                except Exception as e:
                    print(f"  ERROR: {e}")
                    step.notes += f"\nError: {str(e)}"

            print(f"\n{'='*60}")
            print(f"Automation complete!")
            print(f"Screenshots: {screenshots_dir}")
            print(f"{'='*60}\n")

            # Return execution metadata
            return {
                "wallet": self.name,
                "version": self.version,
                "session_id": self.session_id,
                "steps_executed": len(steps_to_run),
                "timestamp": datetime.now().isoformat(),
                "output_dir": str(self.config.output_dir),
                "screenshots_dir": str(screenshots_dir),
            }

        finally:
            # Always disconnect
            self.disconnect()

    def get_steps(self, include_omitted: bool = False, sections: Optional[List[str]] = None) -> List[Step]:
        """Get all steps in the workflow

        Args:
            include_omitted: If False (default), exclude steps marked with omit_from_output
            sections: Filter to specific sections (default: use last_run_sections if available)
        """
        steps = self.steps

        # Use provided sections, or fall back to last run sections
        filter_sections = sections if sections is not None else self.last_run_sections

        # Filter by sections if specified
        if filter_sections is not None:
            steps = [s for s in steps if s.section in filter_sections]

        # Filter out omitted steps unless explicitly requested
        if not include_omitted:
            steps = [s for s in steps if not s.omit_from_output]

        return steps

    def export_metadata(self) -> Dict[str, Any]:
        """Export workflow metadata for documentation generation"""
        return {
            "wallet": {
                "name": self.name,
                "version": self.version,
                "app_path": self.app_path,
            },
            "session": {
                "id": self.session_id,
                "timestamp": datetime.now().isoformat(),
            },
            "steps": [
                {
                    "number": step.step_number,
                    "name": step.name,
                    "description": step.description,
                    "action": step.action,
                    "section": step.section,
                    "omit_from_output": step.omit_from_output,
                    "screenshot": str(step.screenshot_path) if step.screenshot_path else None,
                    "annotated_screenshot": str(step.annotated_screenshot_path) if step.annotated_screenshot_path else None,
                    "annotations": [
                        {
                            "type": ann.type,
                            "target": ann.target,
                            "label": ann.label,
                            "color": ann.color,
                        }
                        for ann in step.annotations
                    ],
                    "flags": step.flags,
                    "notes": step.notes,
                }
                for step in self.steps
            ]
        }


class AppiumAutomation(BaseAutomation):
    """Appium-based automation for apps with accessibility API support"""

    def __init__(
        self,
        name: str,
        app_path: str,
        version: str = "1.0.0",
        config: Optional[WalletConfig] = None
    ):
        super().__init__(name, app_path, version, config)
        self.driver: Optional[webdriver.Remote] = None
    
    def connect(self):
        """Initialize Appium connection"""
        print(f"Connecting to Appium server...")
        
        # Configure options based on platform
        system = platform.system()
        
        if system == "Darwin":  # macos
            options = Mac2Options()
            options.bundle_id = self._get_bundle_id()
            # Alternative: use app path
            # options.app = self.app_path
        else:
            raise NotImplementedError(f"Platform {system} not yet supported")
        
        # Set capabilities
        options.new_command_timeout = 300
        options.platform_name = "Mac"
        
        # Connect to Appium server
        self.driver = webdriver.Remote(
            command_executor='http://127.0.0.1:4723',
            options=options
        )
        
        self.driver.implicitly_wait(self.config.implicit_wait)
        print(f"Connected to {self.name}")
        
        # Wait for app to start
        time.sleep(self.config.startup_wait)
    
    def disconnect(self):
        """Close Appium connection and terminate app"""
        if self.driver:
            print("Disconnecting from Appium...")
            try:
                # Try to close the app gracefully first
                try:
                    bundle_id = self._get_bundle_id()
                    if bundle_id:
                        self.driver.terminate_app(bundle_id)
                        time.sleep(0.5)  # Give app time to close
                except Exception:
                    pass  # App might already be closed
                
                # Delete the session (this should clean up WDA)
                try:
                    session_id = self.driver.session_id
                    self.driver.quit()
                    print(f"✓ Session {session_id} closed")
                except Exception as e:
                    print(f"  Warning: Error during quit: {e}")
                
                # Small delay to let WDA fully clean up
                time.sleep(1)
                
            except Exception as e:
                print(f"Warning: Error during disconnect: {e}")
            finally:
                self.driver = None
    
    def _get_bundle_id(self) -> str:
        """Extract bundle ID from app path (macOS specific)"""
        # Try to read from Info.plist
        import plistlib
        info_plist = Path(self.app_path) / "Contents" / "Info.plist"
        
        if info_plist.exists():
            with open(info_plist, 'rb') as f:
                plist = plistlib.load(f)
                return plist.get('CFBundleIdentifier', '')
        
        # Fallback: derive from app name
        app_name = Path(self.app_path).stem
        return f"com.{app_name.lower()}.app"
    
    def _find_element(self, selector: str, timeout: int = 10):
        """Find element with various strategies"""
        # Try different selector strategies
        strategies = [
            (By.ACCESSIBILITY_ID, selector),
            (By.NAME, selector),
            (By.XPATH, selector),
            (By.CLASS_NAME, selector),
        ]
        
        for by, value in strategies:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return element
            except TimeoutException:
                continue
        
        raise NoSuchElementException(f"Could not find element: {selector}")
    
    def _execute_step(self, step: Step, screenshots_dir: Path = None):
        """Execute a single automation step"""
        print(f"\nStep {step.step_number}: {step.name}")
        print(f"  Action: {step.action}")

        # Wait before action (let UI settle)
        if step.wait_before > 0:
            time.sleep(step.wait_before)

        # Capture screenshot BEFORE action (shows state user will interact with)
        if step.screenshot:
            time.sleep(self.config.screenshot_delay)
            self._capture_screenshot(step, screenshots_dir)

        # Execute action
        if step.action == "launch":
            # App should already be launched via connect()
            pass

        elif step.action == "click":
            if step.target:
                element = self._find_element(step.target)
                element.click()
                print(f"  Clicked: {step.target}")

        elif step.action == "type":
            if step.target and step.value:
                element = self._find_element(step.target)
                element.clear()
                element.send_keys(step.value)
                print(f"  Typed '{step.value}' into: {step.target}")

        elif step.action == "wait":
            wait_time = float(step.value) if step.value else 1.0
            time.sleep(wait_time)
            print(f"  Waited {wait_time} seconds")

        elif step.action == "screenshot":
            # Already captured above
            pass

        elif step.action == "custom":
            print(f"  Custom action: {step.notes}")

        # Wait after action (let next state load)
        if step.wait_after > 0:
            time.sleep(step.wait_after)
        
        # Store element bounds for annotations
        if step.target and step.annotations:
            try:
                element = self._find_element(step.target)
                location = element.location
                size = element.size
                step.element_bounds = {
                    "x": location['x'],
                    "y": location['y'],
                    "width": size['width'],
                    "height": size['height']
                }
            except Exception as e:
                print(f"  Warning: Could not get element bounds: {e}")
        
        step.timestamp = datetime.now().isoformat()
    
    def _capture_screenshot(self, step: Step, screenshots_dir: Path = None):
        """Capture screenshot for a step"""
        if screenshots_dir is None:
            screenshots_dir = self.config.screenshots_dir

        # Include section name to avoid collisions between steps with similar names
        # Format: section_stepname.png or stepname.png if no section
        if step.section:
            filename = f"{self._sanitize_filename(step.section)}_{self._sanitize_filename(step.name)}.png"
        else:
            filename = f"{self._sanitize_filename(step.name)}.png"
        screenshot_path = screenshots_dir / filename
        
        # Capture full screenshot
        self.driver.save_screenshot(str(screenshot_path))
        
        # Apply manual crop region if specified
        if step.crop_region:
            try:
                from PIL import Image
                x, y, width, height = step.crop_region
                
                img = Image.open(screenshot_path)
                cropped = img.crop((x, y, x + width, y + height))
                cropped.save(screenshot_path)
                print(f"  Screenshot cropped to region: {step.crop_region}")
            except Exception as e:
                print(f"  Warning: Could not crop to region: {e}")
        
        # Get window bounds if crop requested (experimental)
        elif step.crop_to_window:
            try:
                # Get all windows and find the app window (not WDA overlay)
                windows = self.driver.find_elements("class name", "XCUIElementTypeWindow")
                app_window = None
                
                # Skip the first window (usually WDA overlay), find the actual app
                for window in windows:
                    try:
                        # Check if this window belongs to our app
                        # The app window typically has a larger size than the overlay
                        size = window.size
                        if size['width'] > 100 and size['height'] > 100:
                            # Additional check: try to get the window title/identifier
                            app_window = window
                            break
                    except Exception:
                        continue
                
                if app_window:
                    location = app_window.location
                    size = app_window.size
                    step.window_bounds = {
                        "x": location['x'],
                        "y": location['y'],
                        "width": size['width'],
                        "height": size['height']
                    }
                    print(f"  Window bounds: {step.window_bounds}")
                    
                    # Crop the screenshot to window bounds
                    from PIL import Image
                    img = Image.open(screenshot_path)
                    
                    # Get actual screen dimensions to handle retina displays
                    img_width, img_height = img.size
                    
                    # Calculate crop coordinates (handle 2x retina scaling)
                    scale_x = img_width / self.driver.get_window_size()['width']
                    scale_y = img_height / self.driver.get_window_size()['height']
                    
                    x1 = int(step.window_bounds['x'] * scale_x)
                    y1 = int(step.window_bounds['y'] * scale_y)
                    x2 = int((step.window_bounds['x'] + step.window_bounds['width']) * scale_x)
                    y2 = int((step.window_bounds['y'] + step.window_bounds['height']) * scale_y)
                    
                    cropped = img.crop((x1, y1, x2, y2))
                    cropped.save(screenshot_path)
                    print(f"  Screenshot cropped to app window")
                else:
                    print(f"  Warning: Could not find app window, using full screenshot")
            except Exception as e:
                print(f"  Warning: Could not crop to window: {e}")
        
        step.screenshot_path = screenshot_path
        print(f"  Screenshot saved: {screenshot_path.name}")


class PyAutoGUIAutomation(BaseAutomation):
    """PyAutoGUI-based automation for apps without accessibility API support

    Uses coordinate-based interaction instead of element selectors.
    Ideal for apps that don't expose accessibility APIs.
    """

    def __init__(
        self,
        name: str,
        app_path: str,
        version: str = "1.0.0",
        config: Optional[WalletConfig] = None,
        scale_factor: float = 2.0
    ):
        super().__init__(name, app_path, version, config)
        self.app_process = None
        self.scale_factor = scale_factor  # Retina DPI scaling

        # Import pyautogui lazily to avoid dependency if not used
        try:
            import pyautogui
            self.pyautogui = pyautogui
            # Configure PyAutoGUI settings
            pyautogui.PAUSE = 0.5  # Add delay between actions
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        except ImportError:
            raise ImportError(
                "PyAutoGUI is required for PyAutoGUIAutomation. "
                "Install it with: pip install pyautogui"
            )

    def connect(self):
        """Launch the application"""
        if self.config.app_paths:
            print(f"Launching: {self.app_path}")
            self.app_process = subprocess.Popen([self.app_path])
            print("✓ App launched\n")
        time.sleep(self.config.startup_wait)  # Wait for app to start

    def disconnect(self):
        """Cleanup after automation"""
        if self.app_process:
            print("\nClosing app...")
            self.app_process.terminate()
            try:
                self.app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.app_process.kill()
            self.app_process = None

    def _execute_step(self, step: Step, screenshots_dir: Path):
        """Execute a single step"""
        print(f"Step {step.step_number}: {step.name}")

        # Wait before action (let UI settle)
        if step.wait_before > 0:
            time.sleep(step.wait_before)

        # Capture screenshot BEFORE action (shows state user will interact with)
        if step.screenshot:
            self._capture_screenshot(step, screenshots_dir)

        # Execute action
        if step.action == "click" and step.target:
            # Parse target as coordinates: (x, y)
            x, y = step.target
            self.pyautogui.click(x, y, clicks=step.clicks)
            print(f"  Clicked at: ({x}, {y})")

        elif step.action == "type" and step.value:
            self.pyautogui.write(step.value, interval=0.001)
            print(f"  Typed: {step.value}")

        elif step.action == "wait":
            wait_time = float(step.value) if step.value else 1.0
            time.sleep(wait_time)
            print(f"  Waited {wait_time} seconds")

        # Wait after action (let next state load)
        if step.wait_after > 0:
            time.sleep(step.wait_after)

        step.timestamp = datetime.now().isoformat()

    def _capture_screenshot(self, step: Step, screenshots_dir: Path):
        """Capture screenshot"""
        # Include section name to avoid collisions between steps with similar names
        # Format: section_stepname.png or stepname.png if no section
        if step.section:
            filename = f"{self._sanitize_filename(step.section)}_{self._sanitize_filename(step.name)}.png"
        else:
            filename = f"{self._sanitize_filename(step.name)}.png"
        screenshot_path = screenshots_dir / filename

        # Take screenshot
        screenshot = self.pyautogui.screenshot()
        time.sleep(self.config.screenshot_delay)

        # Apply crop if specified
        if step.crop_region:
            x, y, width, height = step.crop_region
            # Apply scale factor for retina displays
            scaled_x = int(x * self.scale_factor)
            scaled_y = int(y * self.scale_factor)
            scaled_width = int(width * self.scale_factor)
            scaled_height = int(height * self.scale_factor)
            screenshot = screenshot.crop((
                scaled_x,
                scaled_y,
                scaled_x + scaled_width,
                scaled_y + scaled_height
            ))
            print(f"  Cropped to: {step.crop_region} (scaled by {self.scale_factor}x)")

        screenshot.save(screenshot_path)
        step.screenshot_path = screenshot_path
        print(f"  Screenshot saved: {screenshot_path.name}")


# Backward compatibility alias
WalletAutomation = AppiumAutomation


def create_automation(
    name: str,
    app_path: str,
    backend: str = "appium",
    version: str = "1.0.0",
    config: Optional[WalletConfig] = None,
    **kwargs
) -> BaseAutomation:
    """Factory function to create automation instances

    Args:
        name: Wallet/app name
        app_path: Path to application
        backend: Automation backend ("appium" or "pyautogui")
        version: App version
        config: Optional WalletConfig instance
        **kwargs: Additional backend-specific arguments

    Returns:
        BaseAutomation instance (AppiumAutomation or PyAutoGUIAutomation)

    Example:
        # Appium automation
        wallet = create_automation("MyWallet", "/path/to/app.app", backend="appium")

        # PyAutoGUI automation with custom scale factor
        wallet = create_automation("MyWallet", "/path/to/app", backend="pyautogui", scale_factor=2.0)
    """
    if backend == "appium":
        return AppiumAutomation(name, app_path, version, config)
    elif backend == "pyautogui":
        return PyAutoGUIAutomation(name, app_path, version, config, **kwargs)
    else:
        raise ValueError(
            f"Unknown backend: {backend}. "
            f"Supported backends: 'appium', 'pyautogui'"
        )
