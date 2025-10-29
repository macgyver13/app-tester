"""
Markdown documentation generator with template support
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, Template

from .automation import Step
from .config import WalletConfig


class DocumentationGenerator:
    """Generate publication-ready Markdown documentation from automation steps"""
    
    def __init__(self, config: WalletConfig, template_dir: Optional[Path] = None):
        self.config = config
        self.template_dir = template_dir or Path("templates")
        self.env = self._setup_jinja_env()
    
    def _setup_jinja_env(self) -> Environment:
        """Configure Jinja2 environment"""
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filters
        env.filters['basename'] = lambda p: Path(p).name
        env.filters['relpath'] = lambda p, base: Path(p).relative_to(base)
        
        return env
    
    def generate(
        self,
        steps: List[Step],
        output_path: Optional[Path] = None,
        staging: bool = True,
        sections_only: Optional[List[str]] = None
    ) -> Path:
        """Generate Markdown documentation from steps
        
        Args:
            steps: List of steps to document
            output_path: Override default output path
            staging: Use staging directory if True
            sections_only: If specified, only generate these sections (updates section files only)
        """
        
        # Determine output directory
        if output_path is None:
            if staging:
                output_dir = self.config.staging_dir
            else:
                output_dir = self.config.output_dir
            output_path = output_dir / "user-guide.md"
        else:
            output_dir = output_path.parent
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # If sections_only is specified, generate section files only
        if sections_only:
            self._generate_section_files(steps, output_dir, staging, sections_only)
            # Rebuild master file from all existing section files
            self._generate_master_file(output_dir, staging)
            print(f"\nSection documentation updated: {output_dir}")
        else:
            # Generate complete documentation (backward compatible)
            self._generate_complete_doc(steps, output_path, staging)
            print(f"\nDocumentation generated: {output_path}")
        
        # Also save metadata as JSON
        metadata_path = output_dir / "metadata.json"
        template_data = self._prepare_template_data(steps, staging=staging)
        # TODO: if has_sections is true, don't include steps
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, default=str)
        
        return output_path
    
    def _prepare_template_data(self, steps: List[Step], staging: bool = True) -> Dict[str, Any]:
        """Prepare data dictionary for template rendering"""
        
        # Process steps (filter out omitted steps)
        processed_steps = []
        for step in steps:
            # Skip steps marked as omit_from_output
            if step.omit_from_output:
                continue
                
            step_data = {
                "number": step.step_number,
                "name": step.name,
                "description": step.description,
                "section": step.section,
                "flags": step.flags,
                "notes": step.notes,
                "screenshot": None,
                "screenshot_relative": None,
            }
            
            # Use annotated screenshot if available, otherwise original
            screenshot = step.annotated_screenshot_path or step.screenshot_path
            if screenshot:
                step_data["screenshot"] = str(screenshot)
                # Calculate relative path from the markdown file's location
                try:
                    # Determine where markdown will be (staging or output)
                    if staging:
                        markdown_dir = self.config.staging_dir
                    else:
                        markdown_dir = self.config.output_dir
                    
                    # Make relative path from markdown location to screenshot
                    rel_path = screenshot.relative_to(markdown_dir)
                    step_data["screenshot_relative"] = str(rel_path)
                except ValueError:
                    # Fallback: assume screenshots are in sibling directory
                    step_data["screenshot_relative"] = f"screenshots/{screenshot.name}"
            
            processed_steps.append(step_data)
        
        # Group steps by section
        sections = {}
        for step in processed_steps:
            section_name = step["section"] or "main"
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(step)
        
        # Categorize steps by flags
        new_features = [s for s in processed_steps if "NEW" in s["flags"]]
        changed_features = [s for s in processed_steps if "CHANGED" in s["flags"]]
        
        return {
            "title": self.config.title,
            "wallet_name": self.config.name,
            "description": self.config.description,
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "steps": processed_steps,
            "sections": sections,
            "has_sections": len(sections) > 1,
            "total_steps": len(processed_steps),
            "new_features": new_features,
            "changed_features": changed_features,
            "has_new_features": len(new_features) > 0,
            "has_changed_features": len(changed_features) > 0,
            "source_url": self.config.source_url,
            "build_instructions": self.config.build_instructions,
            "screenshot_max_height": self.config.screenshot_max_height,
            "troubleshooting": self.config.troubleshooting,
        }
    
    def generate_index(self, wallet_docs: List[Dict[str, Any]], output_path: Path):
        """Generate an index page for all wallet documentation"""
        template_data = {
            "title": "Bitcoin Wallet Documentation",
            "wallets": wallet_docs,
            "total_wallets": len(wallet_docs),
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        template = self.env.get_template("index.md.j2")
        content = template.render(**template_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Index generated: {output_path}")

    def _generate_complete_doc(self, steps: List[Step], output_path: Path, staging: bool):
        """Generate a complete documentation file (original behavior)"""
        # Prepare template data
        template_data = self._prepare_template_data(steps, staging=staging)

        # When not using sections, we pass steps directly to the master template
        # which will render them in non-sectioned mode
        template_data['sections'] = None  # Signal to use non-sectioned rendering

        # Load and render template (now always use master template)
        template = self.env.get_template("master_guide.md.j2")
        markdown_content = template.render(**template_data)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def _generate_section_files(self, steps: List[Step], output_dir: Path, staging: bool, sections: List[str]):
        """Generate individual section markdown files"""
        sections_dir = output_dir / "sections"
        sections_dir.mkdir(parents=True, exist_ok=True)
        
        # Group steps by section
        steps_by_section = {}
        for step in steps:
            if step.omit_from_output:
                continue
            section = step.section or "main"
            if section not in steps_by_section:
                steps_by_section[section] = []
            steps_by_section[section].append(step)
        
        # Generate markdown for each section
        for section_name in sections:
            if section_name not in steps_by_section:
                print(f"  Warning: No steps found for section '{section_name}'")
                continue
            
            section_steps = steps_by_section[section_name]
            section_file = sections_dir / f"{section_name}.md"
            
            # Get section config if available
            section_config = None
            if hasattr(self.config, 'sections') and self.config.sections:
                section_config = self.config.sections.get(section_name)

            # Extract title and description from SectionConfig or use defaults
            if section_config:
                section_title = section_config.title
                section_description = section_config.description
            else:
                section_title = section_name.title()
                section_description = ''

            section_data = {
                "section_name": section_name,
                "section_title": section_title,
                "section_description": section_description,
                "steps": self._process_steps(section_steps, output_dir, staging),
                "screenshot_max_height": self.config.screenshot_max_height,
            }

            # Render section template
            template = self.env.get_template("section.md.j2")
            content = template.render(**section_data)
            
            with open(section_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  Generated: {section_file.name}")
    
    def _generate_master_file(self, output_dir: Path, staging: bool):
        """Generate master user-guide.md that includes all section files"""
        sections_dir = output_dir / "sections"

        # Use config section order if available, otherwise fallback to alphabetical
        section_order = []
        if hasattr(self.config, 'sections') and self.config.sections:
            # Preserve order from config.yaml
            section_order = list(self.config.sections.keys())
        else:
            # Fallback: find all existing section files and sort alphabetically
            if sections_dir.exists():
                section_order = sorted([f.stem for f in sections_dir.glob("*.md")])

        # Read section content in config order
        sections_content = []
        for section_name in section_order:
            section_file = sections_dir / f"{section_name}.md"

            # Skip if section file doesn't exist
            if not section_file.exists():
                continue

            with open(section_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Fix relative paths for master file (master is one level up from sections)
            # Section files use ../screenshots/ but master file needs screenshots/
            content = content.replace('src="../screenshots/', 'src="screenshots/')

            # Get section title from config if available
            section_title = section_name.title()
            if hasattr(self.config, 'sections') and self.config.sections:
                section_config = self.config.sections.get(section_name)
                if section_config:
                    section_title = section_config.title

            sections_content.append({
                "name": section_name,
                "title": section_title,
                "content": content,
            })

        # Get section configs if available
        section_configs = {}
        if hasattr(self.config, 'sections') and self.config.sections:
            section_configs = self.config.sections
        
        # Prepare master template data
        master_data = {
            "title": self.config.title,
            "wallet_name": self.config.name,
            "description": self.config.description,
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "sections": sections_content,
            "section_configs": section_configs,
            "source_url": self.config.source_url,
            "build_instructions": self.config.build_instructions,
            "screenshot_max_height": self.config.screenshot_max_height,
            "troubleshooting": self.config.troubleshooting,
        }
        
        # Render master template
        template = self.env.get_template("master_guide.md.j2")
        content = template.render(**master_data)
        
        master_file = output_dir / "user-guide.md"
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Generated: user-guide.md (master)")
    
    def _process_steps(self, steps: List[Step], output_dir: Path, staging: bool) -> List[Dict[str, Any]]:
        """Process steps for template rendering"""
        processed_steps = []
        for step in steps:
            step_data = {
                "number": step.step_number,
                "name": step.name,
                "description": step.description,
                "section": step.section,
                "flags": step.flags,
                "notes": step.notes,
                "screenshot": None,
                "screenshot_relative": None,
            }
            
            # Use annotated screenshot if available, otherwise original
            screenshot = step.annotated_screenshot_path or step.screenshot_path
            if screenshot:
                step_data["screenshot"] = str(screenshot)
                try:
                    rel_path = screenshot.relative_to(output_dir)
                    step_data["screenshot_relative"] = str(rel_path)
                except ValueError:
                    step_data["screenshot_relative"] = f"screenshots/{screenshot.name}"
            
            processed_steps.append(step_data)
        
        return processed_steps
