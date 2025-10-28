"""
Template wallet automation script

Copy this template to create new wallet documentation:
1. cp -r wallets/template wallets/<your-wallet>
2. Edit config.yaml with your wallet details
3. Choose your approach: config-driven (recommended) or code-driven
4. Run: python scripts/run_wallet.py wallets/<your-wallet>/setup_walkthrough.py

NEW: This template supports two approaches:
- Config-driven: Define steps in config.yaml (RECOMMENDED for most wallets)
- Code-driven: Define steps in Python code (for complex logic)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.automation import WalletAutomation, PyAutoGUIAutomation, Step, Annotation
from core.config import WalletConfig


def create_automation():
    """Define the wallet automation workflow"""

    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = WalletConfig.from_yaml(str(config_path))

    # Initialize automation
    # Choose based on your wallet type:
    # - WalletAutomation: For Appium-based GUI automation (macOS apps with UI elements)
    # - PyAutoGUIAutomation: For coordinate-based automation (any desktop app)

    # Appium-based (recommended for apps with accessible UI elements)
    wallet = WalletAutomation(
        name=config.name,
        app_path=config.get_app_path(),
        version="1.0.0",
        config=config
    )

    # OR PyAutoGUI-based (for coordinate-based automation)
    # wallet = PyAutoGUIAutomation(
    #     name=config.name,
    #     app_path=config.get_app_path(),
    #     version="1.0.0",
    #     config=config,
    #     scale_factor=2.0  # Set for Retina displays
    # )

    # ============================================================================
    # APPROACH 1: CONFIG-DRIVEN (RECOMMENDED)
    # ============================================================================
    # Load all steps from config.yaml - this is the preferred approach!
    #
    # Benefits:
    # - Single source of truth in config.yaml
    # - Easy to update coordinates and descriptions
    # - Non-developers can modify the automation
    # - Cleaner, more maintainable code
    #
    # To use this approach:
    # 1. Define sections, coordinates, and steps in config.yaml
    # 2. Uncomment the line below
    # 3. Comment out or remove the code-driven approach

    wallet.add_steps_from_config()  # Load all sections from config

    # Or load specific sections only:
    # wallet.add_steps_from_config('setup')
    # wallet.add_steps_from_config('usage')

    # ============================================================================
    # APPROACH 2: CODE-DRIVEN (for complex logic or dynamic steps)
    # ============================================================================
    # Define steps directly in Python code when you need:
    # - Complex conditional logic
    # - Dynamic step generation
    # - Programmatic coordinate calculation
    # - Advanced annotations
    #
    # Comment out the above `add_steps_from_config()` if using this approach

    # # Step 1: Launch application
    # wallet.add_step(
    #     Step(
    #         name="Launch Application",
    #         description="Open the wallet application from your Applications folder. "
    #                    "The application will start and display the welcome screen.",
    #         action="launch",
    #         screenshot=True,
    #         section="setup",
    #         annotations=[
    #             Annotation.text("Main Window", position=(50, 50), color="blue")
    #         ]
    #     )
    # )

    # # Step 2: Click create wallet button
    # wallet.add_step(
    #     Step(
    #         name="Create New Wallet",
    #         description="Click the 'Create New Wallet' button to begin the wallet setup process.",
    #         action="click",
    #         target="create_wallet_button",  # Appium selector or (x, y) coordinates
    #         screenshot=True,
    #         section="setup",
    #         annotations=[
    #             Annotation.arrow(target="create_wallet_button", label="Click here", color="red"),
    #             Annotation.box(target="create_wallet_button", color="green")
    #         ],
    #         flags=["NEW"]  # Mark as new feature if applicable
    #     )
    # )

    # # Step 3: Enter wallet name
    # wallet.add_step(
    #     Step(
    #         name="Enter Wallet Name",
    #         description="Type a descriptive name for your wallet.",
    #         action="type",
    #         target="wallet_name_field",
    #         value="My Bitcoin Wallet",
    #         screenshot=True,
    #         section="setup",
    #         annotations=[
    #             Annotation.highlight(target="wallet_name_field", color="yellow"),
    #             Annotation.number(number=1, target="wallet_name_field", color="blue")
    #         ]
    #     )
    # )

    # # For PyAutoGUI coordinate-based automation, use tuples for targets:
    # # wallet.add_step(
    # #     Step(
    # #         name="Click Button",
    # #         description="Click the button at coordinates",
    # #         action="click",
    # #         target=(400, 300),  # (x, y) screen coordinates
    # #         screenshot=True,
    # #         crop_region=(100, 100, 800, 600),  # Optional crop: (x, y, width, height)
    # #         section="setup"
    # #     )
    # # )

    # ============================================================================
    # HYBRID APPROACH (mix config and code)
    # ============================================================================
    # You can also mix both approaches:
    # - Load most steps from config
    # - Add complex steps programmatically
    #
    # Example:
    # wallet.add_steps_from_config('setup')  # Load setup from config
    # wallet.add_step(Step(...))  # Add custom step with complex logic
    # wallet.add_steps_from_config('usage')  # Load usage from config

    return wallet


# Create wallet instance at module level for the script loader
wallet = create_automation()


if __name__ == "__main__":
    """
    Run the automation directly (without the pipeline script)

    For Appium-based automation:
    - Appium server must be running on localhost:4723
    - Start it with: appium

    For PyAutoGUI-based automation:
    - No server needed
    - Ensure the app is in the correct position on screen
    """

    try:
        metadata = wallet.run()
        print("\n" + "="*70)
        print("✓ Automation completed successfully!")
        print(f"Session ID: {metadata['session_id']}")
        print(f"Screenshots: {metadata['screenshots_dir']}")
        print("="*70)
    except Exception as e:
        print(f"\n✗ Automation failed: {e}")
        print("\nTroubleshooting:")
        print("1. For Appium: Ensure Appium is running: appium")
        print("2. Verify the wallet application is installed")
        print("3. Check element selectors or coordinates in config/script")
        print("4. For Appium: Use Appium Inspector to find correct selectors")
        print("5. For PyAutoGUI: Verify screen coordinates and scale_factor")
        import traceback
        traceback.print_exc()
        sys.exit(1)
