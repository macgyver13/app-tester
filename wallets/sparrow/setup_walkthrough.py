#!/usr/bin/env python3
"""
PyAutoGUI-based automation for BlindBitDesktop - Config-Driven Approach
This version loads all steps from config.yaml instead of defining them in Python
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.automation import PyAutoGUIAutomation, Step
from core.config import WalletConfig


def create_automation():
    """Create BlindBit Desktop automation using config-driven approach"""

    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = WalletConfig.from_yaml(str(config_path))

    # Initialize automation using core PyAutoGUIAutomation
    wallet = PyAutoGUIAutomation(
        name=config.name,
        app_path=config.get_app_path(),
        version="1.0.0",
        config=config  # scale_factor read from config.display_scale
    )

    # Load all automation steps from config
    wallet.add_steps_from_config()

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
