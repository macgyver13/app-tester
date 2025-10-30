#!/usr/bin/env python3
"""
Review and approve staged documentation
"""

import sys
import shutil
import json
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import WalletConfig
from core.generator import DocumentationGenerator


def list_staged_docs(staging_dir: Path):
    """List all documentation in staging area"""
    if not staging_dir.exists():
        print(f"Staging directory not found: {staging_dir}")
        return []
    
    staged = []
    for wallet_dir in staging_dir.iterdir():
        if wallet_dir.is_dir():
            doc_path = wallet_dir / "user-guide.md"
            if doc_path.exists():
                staged.append(wallet_dir)
    
    return staged


def show_diff(staging_path: Path, output_path: Path):
    """Show differences between staged and published versions"""
    if not output_path.exists():
        print("  No published version exists (new documentation)")
        return
    
    # Simple comparison - just show file sizes for now
    staging_size = staging_path.stat().st_size
    output_size = output_path.stat().st_size
    
    print(f"  Staging size: {staging_size} bytes")
    print(f"  Published size: {output_size} bytes")
    
    if staging_size != output_size:
        print("  ⚠️  Files differ in size")


def get_used_screenshots(metadata_path: Path) -> set[str]:
    """Extract list of screenshot filenames from metadata.json"""
    if not metadata_path.exists():
        return set()

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        screenshots = set()
        for step in metadata.get('steps', []):
            screenshot_rel = step.get('screenshot_relative', '')
            if screenshot_rel:
                # Extract just the filename from the relative path
                screenshots.add(Path(screenshot_rel).name)

        return screenshots
    except Exception as e:
        print(f"  Warning: Could not parse metadata.json: {e}")
        return set()


def approve_wallet(wallet_name: str, staging_dir: Path, output_dir: Path):
    """Move wallet documentation from staging to final output"""
    staging_wallet = staging_dir / wallet_name
    output_wallet = output_dir / wallet_name

    if not staging_wallet.exists():
        print(f"Error: Wallet not found in staging: {wallet_name}")
        return False

    # Create output directory
    output_wallet.mkdir(parents=True, exist_ok=True)

    # Get list of used screenshots from metadata
    metadata_path = staging_wallet / "metadata.json"
    used_screenshots = get_used_screenshots(metadata_path)

    # Copy files selectively
    screenshots_copied = 0
    screenshots_skipped = 0

    for item in staging_wallet.iterdir():
        dest = output_wallet / item.name

        # Handle screenshots directory specially
        if item.is_dir() and item.name == "screenshots":
            dest.mkdir(exist_ok=True)

            # Only copy screenshots that are referenced in metadata
            for screenshot in item.iterdir():
                if screenshot.name in used_screenshots:
                    shutil.copy2(screenshot, dest / screenshot.name)
                    screenshots_copied += 1
                else:
                    screenshots_skipped += 1
        elif item.is_dir():
            # Copy other directories as-is
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            # Copy regular files
            shutil.copy2(item, dest)

    print(f"✓ Published: {wallet_name}")
    print(f"  From: {staging_wallet}")
    print(f"  To: {output_wallet}")

    if screenshots_copied > 0 or screenshots_skipped > 0:
        print(f"  Screenshots: {screenshots_copied} copied, {screenshots_skipped} skipped")

    return True


def regenerate_index(output_dir: Path):
    """Regenerate the documentation index (README.md) for all published wallets"""
    print("\nRegenerating documentation index...")

    # Scan output directory for wallet documentation
    wallets = []
    for wallet_dir in output_dir.iterdir():
        # Skip staging and hidden directories
        if wallet_dir.name == "staging" or wallet_dir.name.startswith("."):
            continue

        if not wallet_dir.is_dir():
            continue

        # Look for setup-guide.md (primary) or user-guide.md (legacy)
        guide_path = wallet_dir / "setup-guide.md"
        if not guide_path.exists():
            guide_path = wallet_dir / "user-guide.md"

        if not guide_path.exists():
            continue

        # Load wallet configuration
        config_path = Path("wallets") / wallet_dir.name / "config.yaml"
        wallet_name = wallet_dir.name.replace("_", " ").title()
        description = f"Silent Payment user guide for {wallet_name}"
        platform = ""
        version = None

        if config_path.exists():
            try:
                config = WalletConfig.from_yaml(str(config_path))
                wallet_name = config.name
                description = config.description

                # Extract platforms and format
                if hasattr(config, 'platforms') and config.platforms:
                    # Capitalize platform names (macos -> MacOS)
                    platform_map = {
                        'macos': 'MacOS',
                        'windows': 'Windows',
                        'linux': 'Linux',
                        'ios': 'iOS',
                        'android': 'Android'
                    }
                    formatted_platforms = [
                        platform_map.get(p.lower(), p.title())
                        for p in config.platforms
                    ]
                    platform = ", ".join(formatted_platforms)

                # Extract version if it exists
                version = config.version

            except Exception:
                pass  # Use defaults if config fails to load

        # Load metadata if available
        metadata_file = wallet_dir / "metadata.json"
        last_updated = datetime.now().strftime("%Y-%m-%d")
        total_steps = 0

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    # Use generated_date from metadata (preferred)
                    generated_date = metadata.get('generated_date', '')
                    if generated_date:
                        last_updated = generated_date
                    total_steps = metadata.get('total_steps', 0)
            except Exception:
                pass  # Use defaults if metadata fails to load

        wallets.append({
            "name": wallet_name,
            "description": description,
            "doc_path": f"{wallet_dir.name}/setup-guide.md" if (wallet_dir / "setup-guide.md").exists() else f"{wallet_dir.name}/user-guide.md",
            "last_updated": last_updated,
            "total_steps": total_steps,
            "platform": platform,
            "version": version,
        })

    if not wallets:
        print("  No wallet documentation found to index")
        return

    # Sort wallets alphabetically by name
    wallets.sort(key=lambda w: w["name"])

    # Generate index using DocumentationGenerator
    # Create a minimal config just for the generator
    dummy_config = WalletConfig(name="Index")
    generator = DocumentationGenerator(config=dummy_config)

    index_path = output_dir / "README.md"
    generator.generate_index(wallets, index_path)

    print(f"✓ Updated index: {index_path}")
    print(f"  Indexed {len(wallets)} wallet(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Review and approve staged documentation"
    )
    parser.add_argument(
        "wallet",
        nargs="?",
        help="Wallet name to approve (omit to list all)"
    )
    parser.add_argument(
        "--staging-dir",
        type=Path,
        default=Path("output/staging"),
        help="Staging directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Final output directory"
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Approve and publish the wallet documentation"
    )
    parser.add_argument(
        "--approve-all",
        action="store_true",
        help="Approve all staged documentation"
    )
    
    args = parser.parse_args()
    
    # List staged documentation
    staged = list_staged_docs(args.staging_dir)
    
    if not staged:
        print("No documentation found in staging area.")
        return
    
    # If no wallet specified, list all
    if not args.wallet and not args.approve_all:
        print(f"\n{'='*70}")
        print("Staged Documentation")
        print(f"{'='*70}\n")
        
        for i, wallet_dir in enumerate(staged, 1):
            wallet_name = wallet_dir.name
            doc_path = wallet_dir / "user-guide.md"
            
            print(f"{i}. {wallet_name}")
            print(f"   Path: {doc_path}")
            
            # Check if published version exists
            published_path = args.output_dir / wallet_name / "user-guide.md"
            show_diff(doc_path, published_path)
            print()
        
        print(f"\nTotal: {len(staged)} wallet(s) in staging")
        print("\nTo review a wallet: python scripts/review.py <wallet_name>")
        print("To approve a wallet: python scripts/review.py <wallet_name> --approve")
        print("To approve all: python scripts/review.py --approve-all")
        
        return
    
    # Approve all
    if args.approve_all:
        print(f"\nApproving {len(staged)} wallet(s)...")
        for wallet_dir in staged:
            approve_wallet(wallet_dir.name, args.staging_dir, args.output_dir)
        print(f"\n✓ All staged documentation published")

        # Regenerate documentation index
        regenerate_index(args.output_dir)
        return
    
    # Approve specific wallet
    if args.approve:
        success = approve_wallet(args.wallet, args.staging_dir, args.output_dir)
        if success:
            print(f"\n✓ {args.wallet} has been published")

            # Regenerate documentation index
            regenerate_index(args.output_dir)
        sys.exit(0 if success else 1)
    
    # Show details for specific wallet
    wallet_dir = args.staging_dir / args.wallet
    if not wallet_dir.exists():
        print(f"Error: Wallet not found in staging: {args.wallet}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Review: {args.wallet}")
    print(f"{'='*70}\n")
    
    doc_path = wallet_dir / "user-guide.md"
    if doc_path.exists():
        with open(doc_path, 'r') as f:
            content = f.read()
        
        print(f"Documentation Preview ({len(content)} characters):")
        print("-" * 70)
        
        # Show first 50 lines
        lines = content.split('\n')
        preview_lines = lines[:50]
        print('\n'.join(preview_lines))
        
        if len(lines) > 50:
            print(f"\n... ({len(lines) - 50} more lines)")
        
        print("\n" + "-" * 70)
        
        # Check screenshots
        screenshots_dir = wallet_dir / "screenshots"
        if screenshots_dir.exists():
            screenshots = list(screenshots_dir.glob("*.png"))
            print(f"\nScreenshots: {len(screenshots)}")
            for ss in screenshots[:5]:
                print(f"  - {ss.name}")
            if len(screenshots) > 5:
                print(f"  ... and {len(screenshots) - 5} more")
    
    print(f"\n{'='*70}")
    print(f"To approve: python scripts/review.py {args.wallet} --approve")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
