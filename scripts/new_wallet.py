#!/usr/bin/env python3
"""
Interactive setup wizard for creating new wallet documentation
"""

import sys
from pathlib import Path
import shutil

def main():
    print("\n" + "="*70)
    print("Silent Payment Documentation - New Wallet Wizard")
    print("="*70 + "\n")
    
    # Get wallet name
    wallet_name = input("Enter wallet name (e.g., 'Electrum'): ").strip()
    if not wallet_name:
        print("Error: Wallet name is required")
        sys.exit(1)
    
    # Sanitize name for directory
    wallet_dir_name = wallet_name.lower().replace(" ", "_")
    wallet_dir = Path("wallets") / wallet_dir_name
    
    if wallet_dir.exists():
        print(f"\nError: Wallet directory already exists: {wallet_dir}")
        overwrite = input("Overwrite? (yes/no): ").lower()
        if overwrite != "yes":
            sys.exit(1)
        shutil.rmtree(wallet_dir)
    
    # Copy template
    template_dir = Path("wallets") / "template"
    shutil.copytree(template_dir, wallet_dir)
    print(f"\n✓ Created wallet directory: {wallet_dir}")
    
    # Get wallet details
    print("\n" + "-"*70)
    print("Wallet Configuration")
    print("-"*70 + "\n")
    
    version = input("Wallet version (default: 1.0.0): ").strip() or "1.0.0"
    
    platform = input("Primary platform (macos/linux/windows, default: macos): ").strip().lower() or "macos"
    
    app_path = input(f"Application path on {platform}: ").strip()
    if not app_path:
        if platform == "macos":
            app_path = f"/Applications/{wallet_name}.app"
        elif platform == "linux":
            app_path = f"/usr/bin/{wallet_dir_name}"
        else:
            app_path = f"C:\\Program Files\\{wallet_name}\\{wallet_dir_name}.exe"
    
    source_url = input("Source code URL (optional): ").strip()
    
    description = input("Brief description: ").strip() or f"Complete guide to setting up {wallet_name} Bitcoin wallet"
    
    # Update config.yaml
    config_path = wallet_dir / "config.yaml"
    with open(config_path, 'r') as f:
        config = f.read()
    
    config = config.replace('name: "Example Wallet"', f'name: "{wallet_name}"')
    config = config.replace('title: "Example Wallet Setup Guide"', f'title: "{wallet_name} Setup Guide"')
    config = config.replace('description: "Complete guide to setting up Example Bitcoin wallet"', f'description: "{description}"')
    
    if source_url:
        config = config.replace('source_url: "https://github.com/example/wallet"', f'source_url: "{source_url}"')
    
    # Update app paths
    if platform == "macos":
        config = config.replace('macos: "/Applications/ExampleWallet.app"', f'macos: "{app_path}"')
    elif platform == "linux":
        config = config.replace('linux: "/usr/bin/example-wallet"', f'linux: "{app_path}"')
    else:
        config = config.replace('windows: "C:\\Program Files\\ExampleWallet\\example-wallet.exe"', f'windows: "{app_path}"')
    
    with open(config_path, 'w') as f:
        f.write(config)
    
    print(f"\n✓ Updated configuration: {config_path}")
    
    # Inform about next steps
    print("\n" + "="*70)
    print("✓ Wallet Created Successfully!")
    print("="*70 + "\n")
    
    print("Next steps:\n")
    print(f"1. Edit the automation script:")
    print(f"   {wallet_dir / 'setup_walkthrough.py'}")
    print()
    print("2. Update element selectors to match your wallet's UI")
    print("   - Use Appium Inspector to find selectors")
    print("   - Add/remove steps as needed")
    print()
    print("3. Test the automation:")
    print("   # Terminal 1: Start Appium")
    print("   appium")
    print()
    print("   # Terminal 2: Run automation")
    print(f"   python scripts/run_wallet.py wallets/{wallet_dir_name}/setup_walkthrough.py")
    print()
    print("4. Review generated documentation:")
    print(f"   python scripts/review.py {wallet_dir_name}")
    print()
    print("5. Approve and publish:")
    print(f"   python scripts/review.py {wallet_dir_name} --approve")
    print()
    print("="*70 + "\n")
    
    print("Resources:")
    print(f"  - Wallet README: {wallet_dir / 'README.md'}")
    print("  - Template Guide: wallets/template/README.md")
    print("  - Contributing: CONTRIBUTING.md")
    print("  - Quick Reference: QUICKREF.md")
    print()

if __name__ == "__main__":
    main()
