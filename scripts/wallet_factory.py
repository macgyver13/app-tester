#!/usr/bin/env python3
"""
Generic wallet automation factory - eliminates per-wallet boilerplate

This factory creates wallet automation instances directly from config.yaml,
removing the need for repetitive setup_walkthrough.py files.

Usage:
    from scripts.wallet_factory import create_wallet_from_config

    wallet = create_wallet_from_config(
        config_path=Path("wallets/myapp/config.yaml"),
        automation_type="pyautogui"  # or "appium"
    )
"""

import sys
from pathlib import Path
from typing import Union

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.automation import PyAutoGUIAutomation, WalletAutomation
from core.config import WalletConfig


def create_wallet_from_config(
    config_path: Union[str, Path],
    automation_type: str = "pyautogui",
    version: str = "1.0.0"
) -> Union[PyAutoGUIAutomation, WalletAutomation]:
    """
    Factory function to create automation instance from config.yaml

    Args:
        config_path: Path to wallet config.yaml file
        automation_type: Type of automation ("pyautogui" or "appium")
        version: Wallet version string

    Returns:
        Configured wallet automation instance with steps loaded from config

    Raises:
        ValueError: If automation_type is invalid
        FileNotFoundError: If config_path doesn't exist
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load configuration
    config = WalletConfig.from_yaml(str(config_path))

    # Create appropriate automation instance
    if automation_type.lower() == "pyautogui":
        wallet = PyAutoGUIAutomation(
            name=config.name,
            app_path=config.get_app_path(),
            version=version,
            config=config
        )
    elif automation_type.lower() == "appium":
        wallet = WalletAutomation(
            name=config.name,
            app_path=config.get_app_path(),
            version=version,
            config=config
        )
    else:
        raise ValueError(
            f"Invalid automation_type: {automation_type}. "
            f"Must be 'pyautogui' or 'appium'"
        )

    # Load all automation steps from config
    wallet.add_steps_from_config()

    return wallet


if __name__ == "__main__":
    """
    Example: Run automation directly from config.yaml

    Usage:
        python scripts/wallet_factory.py wallets/blindbit/config.yaml
        python scripts/wallet_factory.py wallets/blindbit/config.yaml --type appium
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run wallet automation directly from config.yaml"
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to wallet config.yaml"
    )
    parser.add_argument(
        "--type",
        choices=["pyautogui", "appium"],
        default="pyautogui",
        help="Automation type (default: pyautogui)"
    )

    args = parser.parse_args()

    try:
        wallet = create_wallet_from_config(args.config, args.type)
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
