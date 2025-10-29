#!/usr/bin/env python3
"""
Run wallet automation and generate documentation

Supports two input modes:
1. Legacy: Python script (--script wallets/myapp/setup_walkthrough.py)
2. Preferred: Config file (--config wallets/myapp/config.yaml)
"""

import sys
import argparse
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import WalletAutomation, AnnotationEngine, DocumentationGenerator
from scripts.wallet_factory import create_wallet_from_config


def load_wallet_script(script_path: Path):
    """Dynamically load wallet automation script"""
    spec = spec_from_file_location("wallet_script", script_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find WalletAutomation or PyAutoGUIAutomation instance in module
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, WalletAutomation):
            return obj
        # Also check for duck-typed automation classes (PyAutoGUIAutomation, etc.)
        if hasattr(obj, 'run') and hasattr(obj, 'get_steps') and hasattr(obj, 'config'):
            # Check if it's not a class definition itself
            if not isinstance(obj, type):
                return obj
    
    raise ValueError(f"No WalletAutomation instance found in {script_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run wallet automation and generate documentation",
        epilog="""
Examples:
  # Preferred: Use config.yaml directly
  python scripts/run_wallet.py wallets/blindbit/config.yaml

  # Legacy: Use Python script
  python scripts/run_wallet.py --script wallets/myapp/setup_walkthrough.py

  # Generate docs only (no automation)
  python scripts/run_wallet.py wallets/blindbit/config.yaml --docs-only
        """
    )

    # Positional argument can be either config.yaml or script path
    parser.add_argument(
        "input_path",
        type=Path,
        nargs="?",
        help="Path to wallet config.yaml (preferred) or setup script"
    )
    parser.add_argument(
        "--script",
        type=Path,
        help="[LEGACY] Path to wallet automation script (use config.yaml instead)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to wallet config.yaml (can also be passed as positional arg)"
    )
    parser.add_argument(
        "--automation-type",
        choices=["pyautogui", "appium"],
        default="pyautogui",
        help="Automation type when using config.yaml (default: pyautogui)"
    )
    parser.add_argument(
        "--no-annotate",
        action="store_true",
        help="Skip screenshot annotation"
    )
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Skip documentation generation"
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Skip screenshot capture (runs automation without taking screenshots)"
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Generate documentation from existing screenshots without running automation"
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        default=True,
        help="Output to staging area (default: True)"
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        help="Only run specific sections (e.g., --sections setup usage)"
    )

    args = parser.parse_args()

    # Determine input mode: config.yaml (preferred) or script (legacy)
    wallet_script_path = None
    wallet_config_path = None

    # Priority: --config flag > --script flag > positional arg
    # But always check if the path is actually a YAML file first
    if args.config:
        wallet_config_path = args.config
    elif args.script:
        # Check if --script was given a config.yaml (common mistake)
        if args.script.name == "config.yaml" or args.script.suffix in [".yaml", ".yml"]:
            wallet_config_path = args.script
            print(f"Note: Detected YAML file with --script flag, treating as config")
        else:
            wallet_script_path = args.script
    elif args.input_path:
        # Auto-detect based on filename
        if args.input_path.name == "config.yaml" or args.input_path.suffix in [".yaml", ".yml"]:
            wallet_config_path = args.input_path
        else:
            wallet_script_path = args.input_path
    else:
        print("Error: Must provide either config.yaml or script path")
        parser.print_help()
        sys.exit(1)

    # Validate input path exists
    input_path = wallet_config_path or wallet_script_path
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Silent Payment Documentation Pipeline")
    print(f"{'='*70}\n")

    # Load wallet automation
    try:
        if wallet_config_path:
            # NEW: Load directly from config.yaml
            print(f"Loading wallet from config: {wallet_config_path}")
            print(f"Automation type: {args.automation_type}")
            wallet = create_wallet_from_config(
                wallet_config_path,
                automation_type=args.automation_type
            )
        else:
            # LEGACY: Load from Python script
            print(f"Loading wallet script: {wallet_script_path}")
            wallet = load_wallet_script(wallet_script_path)

        # Documentation-only mode: skip automation
        if args.docs_only:
            print("\n⚠️  Documentation-only mode: Skipping automation")
            print("     Using existing screenshots and step definitions")
            steps = wallet.get_steps()

            # We need to populate screenshot paths for existing steps
            # Determine screenshot directory based on staging mode
            if args.staging:
                screenshots_dir = wallet.config.staging_dir / "screenshots"
            else:
                screenshots_dir = wallet.config.screenshots_dir

            # Load existing screenshot metadata if available
            metadata_file = screenshots_dir.parent / "metadata.json"
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    print(f"     Loaded metadata from: {metadata_file}")
            else:
                print(f"     Warning: No metadata.json found at {metadata_file}")
                print(f"     Will attempt to match screenshots by step name")
                metadata = {}

            # Try to match existing screenshots to steps
            for step in steps:
                if step.omit_from_output:
                    continue

                # Sanitize step name to match filename (include section to avoid collisions)
                def sanitize(name):
                    return name.lower().replace(" ", "_").replace("/", "_")[:50]

                if step.section:
                    filename = f"{sanitize(step.section)}_{sanitize(step.name)}.png"
                else:
                    filename = f"{sanitize(step.name)}.png"

                screenshot_path = screenshots_dir / filename

                if screenshot_path.exists():
                    step.screenshot_path = screenshot_path
                    # Check for annotated version
                    annotated_filename = filename.replace(".png", "_annotated.png")
                    annotated_path = screenshots_dir / annotated_filename
                    if annotated_path.exists():
                        step.annotated_screenshot_path = annotated_path
        else:
            # Normal mode: run automation
            # Disable screenshots if requested
            if args.no_screenshots:
                print("\n⚠️  Screenshot capture disabled")
                for step in wallet.get_steps():
                    step.screenshot = False

            # Run automation
            print("\n" + "="*70)
            print("PHASE 1: Automation")
            print("="*70)
            metadata = wallet.run(staging=args.staging, sections=args.sections)

            steps = wallet.get_steps()
            print(f"\nCaptured {len(steps)} steps")
        
        # Determine screenshot directory based on staging mode
        if args.staging:
            screenshots_dir = wallet.config.staging_dir / "screenshots"
        else:
            screenshots_dir = wallet.config.screenshots_dir

        # Annotate screenshots (skip if no screenshots were taken)
        if not args.no_annotate and not args.no_screenshots:
            print("\n" + "="*70)
            print("PHASE 2: Annotation")
            print("="*70 + "\n")

            # Pass display_scale from config to AnnotationEngine
            engine = AnnotationEngine(display_scale=wallet.config.display_scale)
            annotated = engine.batch_annotate(
                steps,
                screenshots_dir
            )
            print(f"\nAnnotated {len(annotated)} screenshots")

        # Generate documentation
        # In docs-only mode, always generate (that's the point)
        # Otherwise, skip if no-generate flag or no screenshots
        should_generate = args.docs_only or (not args.no_generate and not args.no_screenshots)

        if should_generate:
            print("\n" + "="*70)
            print("PHASE 3: Documentation Generation" if not args.docs_only else "Documentation Generation")
            print("="*70 + "\n")

            generator = DocumentationGenerator(wallet.config)
            output_path = generator.generate(
                steps,
                staging=args.staging,
                sections_only=args.sections  # Pass sections to generator
            )

            print(f"\nGenerated: {output_path}")
        
        print("\n" + "="*70)
        print("✓ Pipeline Complete")
        print("="*70)
        
        if args.staging:
            print(f"\nDocumentation staged at: {wallet.config.staging_dir}")
            print("Review and approve with: python scripts/review.py")
        else:
            print(f"\nDocumentation published to: {wallet.config.output_dir}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
