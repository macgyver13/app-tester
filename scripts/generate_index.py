#!/usr/bin/env python3
"""
Generate documentation index for all wallets

Scans the output/ directory and creates an index (README.md) listing
all available wallet documentation guides.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.generator import DocumentationGenerator
from core.config import WalletConfig


def scan_wallets(output_dir: Path):
    """Scan output directory for wallet documentation"""
    wallets = []

    for wallet_dir in output_dir.iterdir():
        # Skip staging and hidden directories
        if wallet_dir.name == "staging" or wallet_dir.name.startswith("."):
            continue

        if not wallet_dir.is_dir():
            continue

        # Look for setup-guide.md
        guide_path = wallet_dir / "setup-guide.md"
        if not guide_path.exists():
            continue

        # Try to load config to get proper name and description
        wallet_name = wallet_dir.name.replace("_", " ").title()
        description = ""

        # Try various config locations
        config_candidates = [
            Path("wallets") / wallet_dir.name / "config.yaml",
            Path("wallets") / wallet_dir.name.replace("_", "-") / "config.yaml",
            Path("wallets") / wallet_dir.name.replace("_desktop", "") / "config.yaml",
        ]

        config_path = None
        for candidate in config_candidates:
            if candidate.exists():
                config_path = candidate
                break

        if config_path:
            try:
                config = WalletConfig.from_yaml(str(config_path))
                wallet_name = config.name
                description = config.description
            except Exception as e:
                print(f"  Warning: Could not load config for {wallet_dir.name}: {e}")

        # Get last updated from metadata
        metadata_path = wallet_dir / "metadata.json"
        last_updated = datetime.now().strftime("%Y-%m-%d")
        total_steps = 0

        if metadata_path.exists():
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    session_id = metadata.get("session_id", "")
                    if session_id:
                        # session_id format: YYYYMMDD_HHMMSS
                        last_updated = f"{session_id[:4]}-{session_id[4:6]}-{session_id[6:8]}"
                    total_steps = metadata.get("total_steps", 0)
            except Exception as e:
                print(f"  Warning: Could not read metadata for {wallet_dir.name}: {e}")

        wallets.append({
            "name": wallet_name,
            "description": description,
            "doc_path": f"{wallet_dir.name}/setup-guide.md",
            "folder_name": wallet_dir.name,
            "last_updated": last_updated,
            "total_steps": total_steps,
        })

    # Sort by name
    return sorted(wallets, key=lambda w: w["name"])


def main():
    """Generate index of all wallet documentation"""
    output_dir = Path("output")

    print("\n" + "="*70)
    print("Generating Documentation Index")
    print("="*70)

    # Scan for wallet documentation
    print("\nScanning for wallet guides...")
    wallets = scan_wallets(output_dir)

    if not wallets:
        print("⚠️  No wallet documentation found in output/")
        print("    Run automation and approve wallets first.")
        return

    print(f"✓ Found {len(wallets)} wallet guide(s):")
    for wallet in wallets:
        print(f"  - {wallet['name']}")

    # Generate index using template
    print("\nGenerating index...")

    # We need a minimal config for the generator
    from core.config import WalletConfig
    dummy_config = WalletConfig(name="Index")

    generator = DocumentationGenerator(config=dummy_config)
    index_path = output_dir / "README.md"
    generator.generate_index(wallets, index_path)

    print(f"\n✓ Generated: {index_path}")
    print(f"  Listed {len(wallets)} wallet(s)")
    print("="*70)


if __name__ == "__main__":
    main()
