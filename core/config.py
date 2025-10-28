"""
Configuration management for wallet automation and documentation
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class SectionConfig:
    """Configuration for a documentation section"""
    title: str
    description: str
    crop: Optional[tuple] = None  # Default crop region for all steps in this section
    coordinates: Dict[str, tuple] = field(default_factory=dict)  # Named coordinate definitions
    steps: List[Dict[str, Any]] = field(default_factory=list)  # Step definitions


@dataclass
class WalletConfig:
    """Configuration for a wallet documentation project"""

    name: str
    wallet_type: str = "desktop"
    platforms: list = field(default_factory=lambda: ["macos"])
    app_paths: Dict[str, str] = field(default_factory=dict)

    # Automation settings
    startup_wait: int = 3
    screenshot_delay: float = 1.0
    implicit_wait: int = 10
    window_size: tuple = (1200, 800)

    # Documentation settings
    title: str = ""
    description: str = ""
    output_format: str = "markdown"
    embed_images: bool = True
    screenshot_max_height: int = 600  # Max height for screenshots in markdown (pixels)
    sections: Dict[str, SectionConfig] = field(default_factory=dict)  # Section configs
    
    # Build information
    source_url: str = ""
    build_instructions: str = ""
    troubleshooting: str = ""
    
    # Output paths
    output_dir: Path = None
    screenshots_dir: Path = None
    staging_dir: Path = None
    
    def __post_init__(self):
        if not self.title:
            self.title = f"{self.name} Wallet User Guide"
        
        if self.output_dir is None:
            self.output_dir = Path("output") / self.name.lower().replace(" ", "_")
        
        if self.screenshots_dir is None:
            self.screenshots_dir = self.output_dir / "screenshots"
            
        if self.staging_dir is None:
            self.staging_dir = Path("output") / "staging" / self.name.lower().replace(" ", "_")
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "WalletConfig":
        """Load configuration from YAML file"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        wallet_data = data.get('wallet', {})
        automation_data = data.get('automation', {})
        doc_data = data.get('documentation', {})
        build_data = data.get('build', {})

        # Parse sections with enhanced structure
        sections_data = doc_data.get('sections', {})
        sections = {}
        for section_name, section_config in sections_data.items():
            # Convert crop from list to tuple if present
            crop = section_config.get('crop')
            if crop and isinstance(crop, list):
                crop = tuple(crop)

            # Parse coordinates
            coordinates = section_config.get('coordinates', {})
            # Convert coordinate lists to tuples
            parsed_coords = {}
            for coord_name, coord_val in coordinates.items():
                if isinstance(coord_val, list):
                    parsed_coords[coord_name] = tuple(coord_val)
                else:
                    parsed_coords[coord_name] = coord_val

            # Parse steps
            steps = section_config.get('steps', [])
            if not isinstance(steps, list):
                # Handle legacy single-step format or dict format
                steps = [steps] if steps else []

            sections[section_name] = SectionConfig(
                title=section_config.get('title', section_name.title()),
                description=section_config.get('description', ''),
                crop=crop,
                coordinates=parsed_coords,
                steps=steps
            )

        return cls(
            name=wallet_data.get('name', 'Unknown'),
            wallet_type=wallet_data.get('type', 'desktop'),
            platforms=wallet_data.get('platforms', ['macOS']),
            app_paths=wallet_data.get('app_path', {}),
            startup_wait=automation_data.get('startup_wait', 3),
            screenshot_delay=automation_data.get('screenshot_delay', 1.0),
            implicit_wait=automation_data.get('implicit_wait', 10),
            title=doc_data.get('title', ''),
            description=doc_data.get('description', ''),
            output_format=doc_data.get('output_format', 'markdown'),
            embed_images=doc_data.get('embed_images', True),
            screenshot_max_height=doc_data.get('screenshot_max_height', 600),
            sections=sections,
            source_url=build_data.get('source_url', ''),
            build_instructions=build_data.get('build_instructions', ''),
            troubleshooting=doc_data.get('troubleshooting', ''),
        )
    
    def get_app_path(self, platform: Optional[str] = None) -> str:
        """Get application path for current or specified platform"""
        if platform is None:
            import platform as pl
            platform = pl.system().lower()
            if platform == "darwin":
                platform = "macos"
        
        return self.app_paths.get(platform, "")
    
    def ensure_directories(self):
        """Create output directories if they don't exist"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'wallet': {
                'name': self.name,
                'type': self.wallet_type,
                'platforms': self.platforms,
                'app_path': self.app_paths,
            },
            'automation': {
                'startup_wait': self.startup_wait,
                'screenshot_delay': self.screenshot_delay,
                'implicit_wait': self.implicit_wait,
            },
            'documentation': {
                'title': self.title,
                'description': self.description,
                'output_format': self.output_format,
                'embed_images': self.embed_images,
            },
            'build': {
                'source_url': self.source_url,
                'build_instructions': self.build_instructions,
            }
        }
    
    def save(self, output_path: str):
        """Save configuration to YAML file"""
        with open(output_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    def get_section_steps(self, section_name: str) -> List[Dict[str, Any]]:
        """
        Get steps for a specific section with resolved coordinates and crop regions.

        Returns a list of step dictionaries with:
        - All step properties from config
        - Resolved 'target' coordinates (from coordinate references)
        - Inherited crop_region from section if not specified
        - section attribute set to section_name
        """
        if section_name not in self.sections:
            return []

        section = self.sections[section_name]
        resolved_steps = []

        for step_config in section.steps:
            step_dict = step_config.copy()

            # Resolve coordinate reference if target is a string
            target = step_dict.get('target')
            if isinstance(target, str) and target in section.coordinates:
                step_dict['target'] = section.coordinates[target]

            # Inherit crop region from section if not specified
            if 'crop_region' not in step_dict and section.crop:
                step_dict['crop_region'] = section.crop

            # Ensure section is set
            step_dict['section'] = section_name

            resolved_steps.append(step_dict)

        return resolved_steps

    def get_all_steps(self) -> List[Dict[str, Any]]:
        """
        Get all steps from all sections in order.

        Returns steps sorted by section order (as they appear in the config).
        """
        all_steps = []
        for section_name in self.sections.keys():
            all_steps.extend(self.get_section_steps(section_name))
        return all_steps
