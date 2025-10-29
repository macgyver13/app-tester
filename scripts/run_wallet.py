#!/usr/bin/env python3
"""
Run wallet automation and generate documentation
"""

import sys
import argparse
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import WalletAutomation, AnnotationEngine, DocumentationGenerator
from core.config import WalletConfig


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
        description="Run wallet automation and generate documentation"
    )
    parser.add_argument(
        "script",
        type=Path,
        help="Path to wallet automation script"
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
        "--config",
        type=Path,
        help="Path to wallet config.yaml"
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        help="Only run specific sections (e.g., --sections setup usage)"
    )
    
    args = parser.parse_args()
    
    # Validate script path
    if not args.script.exists():
        print(f"Error: Script not found: {args.script}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Bitcoin Wallet Documentation Pipeline")
    print(f"{'='*70}\n")
    
    # Load configuration if provided
    config = None
    if args.config and args.config.exists():
        print(f"Loading configuration: {args.config}")
        config = WalletConfig.from_yaml(str(args.config))
    
    # Load and execute wallet script
    print(f"Loading wallet script: {args.script}")
    try:
        wallet = load_wallet_script(args.script)

        # Override config if provided
        if config:
            wallet.config = config
            wallet.config.ensure_directories()

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
