#!/usr/bin/env python3
"""
PyAutoGUI-based automation for BlindBitDesktop
Uses coordinate-based interaction instead of Appium
"""
import sys
from pathlib import Path
import time
import subprocess
import pyautogui

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import Step, Annotation
from core.config import WalletConfig


class PyAutoGUIAutomation:
    """Automation using PyAutoGUI for apps without accessibility APIs"""
    
    def __init__(self, name: str, app_path: str, version: str = "1.0.0", config=None):
        self.name = name
        self.app_path = app_path
        self.version = version
        self.config = config or WalletConfig(name=name)
        self.steps = []
        self.app_process = None
        self.scale_factor = 2.0 # retina dpi is 2x 
        
        # Setup output directories
        self.config.ensure_directories()
        
        # PyAutoGUI settings
        pyautogui.PAUSE = 0.5  # Add delay between actions
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    
    def add_step(self, step: Step):
        """Add a step to the automation workflow"""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)
        return self
    
    def run(self, staging: bool = True):
        """Execute the automation workflow"""
        print(f"\n{'='*60}")
        print(f"Starting PyAutoGUI automation: {self.name} v{self.version}")
        print(f"Steps: {len(self.steps)}")
        print(f"{'='*60}\n")
        
        # Set screenshot directory
        if staging:
            screenshots_dir = self.config.staging_dir / "screenshots"
        else:
            screenshots_dir = self.config.screenshots_dir
        
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Launch the app
            # self._launch_app()
            
            # Execute steps
            for step in self.steps:
                self._execute_step(step, screenshots_dir)
            
            print(f"\n{'='*60}")
            print(f"Automation complete!")
            print(f"Screenshots: {screenshots_dir}")
            print(f"{'='*60}\n")
            
            return {
                "wallet": self.name,
                "version": self.version,
                "steps_executed": len(self.steps),
                "screenshots_dir": str(screenshots_dir),
            }
        
        finally:
            self._cleanup()
    
    def _launch_app(self):
        """Launch the application"""
        print(f"Launching: {self.app_path}")
        self.app_process = subprocess.Popen([self.app_path])
        time.sleep(3)  # Wait for app to start
        print("✓ App launched\n")
    
    def _execute_step(self, step: Step, screenshots_dir: Path):
        """Execute a single step"""
        print(f"Step {step.step_number}: {step.name}")
        
        # Wait before action
        if step.wait_before > 0:
            time.sleep(step.wait_before)
        
        # Execute action
        if step.action == "click" and step.target:
            # Parse target as coordinates: "x,y"
            x, y = step.target
            pyautogui.click(x, y, clicks=step.clicks)
            print(f"  Clicked at: ({x}, {y})")
        
        elif step.action == "type" and step.value:
            pyautogui.write(step.value, interval=0.005)
            print(f"  Typed: {step.value}")
        
        elif step.action == "wait":
            wait_time = float(step.value) if step.value else 1.0
            time.sleep(wait_time)
            print(f"  Waited {wait_time} seconds")
        
        elif step.action == "screenshot":
            pass  # Handled below
        
        # Wait after action
        if step.wait_after > 0:
            time.sleep(step.wait_after)
        
        # Capture screenshot
        if step.screenshot:
            self._capture_screenshot(step, screenshots_dir)
        
        step.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    def _capture_screenshot(self, step: Step, screenshots_dir: Path):
        """Capture screenshot"""
        filename = f"step_{step.step_number:02d}_{self._sanitize_filename(step.name)}.png"
        screenshot_path = screenshots_dir / filename
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Apply crop if specified
        if step.crop_region:
            x, y, width, height = step.crop_region
            # Apply scale factor for retina displays
            scaled_x = int(x * self.scale_factor)
            scaled_y = int(y * self.scale_factor)
            scaled_width = int(width * self.scale_factor)
            scaled_height = int(height * self.scale_factor)
            screenshot = screenshot.crop((scaled_x, scaled_y, scaled_x + scaled_width, scaled_y + scaled_height))
            print(f"  Cropped to: {step.crop_region} (scaled by {self.scale_factor}x)")
        
        screenshot.save(screenshot_path)
        step.screenshot_path = screenshot_path
        print(f"  Screenshot saved: {screenshot_path.name}")
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert step name to valid filename"""
        return name.lower().replace(" ", "_").replace("/", "_")[:50]
    
    def _cleanup(self):
        """Cleanup after automation"""
        if self.app_process:
            print("\nClosing app...")
            self.app_process.terminate()
            try:
                self.app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.app_process.kill()
    
    def get_steps(self):
        """Get all steps"""
        return self.steps


def create_automation():
    """Create BlindBit Desktop automation"""
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = WalletConfig.from_yaml(str(config_path))
    
    # Initialize automation
    wallet = PyAutoGUIAutomation(
        name=config.name,
        app_path=config.get_app_path(),
        version="1.0.0",
        config=config
    )

    # SETUP_CROP = (639.78515625, 351.98828125, 517.703125, 429.16015625)
    SETUP_COORDS = {
        'create_wallet': (846, 675),
        'import_existing': (903, 612),
        'confirm_seed': (778, 596),
        'input_seed': (781, 478),
        'import_wallet': (772, 527),
        'select_mainnet': (670, 570),
        'continue': (771, 686),
        'select_birthheight': (712, 487),
        'select_oracleaddress': (816, 563),
        'save_continue': (749, 813),
    }

    # Crop region
    CROP = (435.7109375, 271.90234375, 1018.08984375, 689.08203125)

    # Coordinate definitions
    COORDS = {
        'scanning_tab': (460, 330),
        'utxos_tab': (564, 340),
        'send_tab': (623, 335),
        'receive_tab': (685, 334),
        'transactions_tab': (757, 331),
        'settings': (860, 335),
    }

    # Clone repo
    wallet.add_step(
        Step(
            name="Clone repo",
            description="""build golang wallet
            % git clone https://github.com/setavenger/blindbit-desktop.git
            """,
            action="custom",
        )
    )

    # build blindbit-desktop
    wallet.add_step(
        Step(
            name="Compile BlindBit Desktop",
            description="""build golang wallet
            % go build -o blindbit-desktop ./cmd/blindbit-desktop
            """,
            action="custom",
        )
    )

    # setup wallet
    wallet.add_step(
        Step(
            name="Create Wallet",
            description="Select Create New Wallet to generate a seed phase",
            action="click",
            target=SETUP_COORDS['import_wallet'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Create Wallet",
            description="Select Import Existing Wallet",
            action="click",
            target=SETUP_COORDS['import_existing'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Focus Seed Phrase",
            description="",
            action="click",
            target=SETUP_COORDS['input_seed'],
            screenshot=False,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Import Seed Phrase",
            description="Enter seed phase",
            action="type",
            value="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art",
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Import Wallet",
            description="TODO: Describe what this does",
            action="click",
            target=SETUP_COORDS['import_wallet'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Select Network",
            description="TODO: Describe what this does",
            action="click",
            target=SETUP_COORDS['select_mainnet'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Finalize",
            description="TODO: Describe what this does",
            action="click",
            target=SETUP_COORDS['continue'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Setup wallet birthdate",
            description="TODO: Describe what this does",
            action="click",
            target=SETUP_COORDS['select_birthheight'],
            screenshot=False,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Define birth height",
            description="TODO: Describe what this does",
            action="type",
            value="917200",
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Define oracle address",
            description="TODO: Describe what this does",
            action="click",
            clicks=2,
            target=SETUP_COORDS['select_oracleaddress'],
        )
    )

    wallet.add_step(
        Step(
            name="Enter tweak server",
            description="Blindbit Oracle V2",
            action="type",
            value="37.27.123.10:50051",
            wait_before=2,
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Finalize",
            description="Start scan",
            action="click",
            target=SETUP_COORDS['save_continue'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    # Usage
    wallet.add_step(
        Step(
            name="Scanning",
            description="TODO: Describe what this does",
            action="click",
            target=COORDS['scanning_tab'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Settings",
            description="TODO: Describe what this does",
            action="click",
            target=COORDS['settings'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Receive Tab",
            description="TODO: Describe what this does",
            action="click",
            target=COORDS['receive_tab'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Transactions Tab",
            description="TODO: Describe what this does",
            action="click",
            target=COORDS['transactions_tab'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Send Tab",
            description="TODO: Describe what this does",
            action="click",
            target=COORDS['send_tab'],
            screenshot=True,
            crop_region=CROP,
        )
    )

    wallet.add_step(
        Step(
            name="Utxos Tab",
            description="TODO: Describe what this does",
            action="click",
            target=COORDS['utxos_tab'],
            screenshot=True,
            crop_region=CROP,
        )
    )

        # # Step 3: Type example
    # wallet.add_step(
    #     Step(
    #         name="Enter Wallet Name",
    #         description="Enter a name for your wallet.",
    #         action="type",
    #         value="My Test Wallet",  # What to type
    #         screenshot=True,
    #         crop_region=(100, 100, 1200, 800),
    #         annotations=[
    #             Annotation.text("Type wallet name", position=(50, 50), color="green")
    #         ]
    #     )
    # )
    
    return wallet


# Create wallet instance at module level
wallet = create_automation()


if __name__ == "__main__":
    try:
        metadata = wallet.run()
        print("\n" + "="*70)
        print("✓ Automation completed successfully!")
        print(f"Screenshots: {metadata['screenshots_dir']}")
        print("="*70)
    except Exception as e:
        print(f"\n✗ Automation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
