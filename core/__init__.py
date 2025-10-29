"""
Silent Payment Documentation Pipeline - Core Modules
"""

__version__ = "0.1.0"

from .automation import (
    BaseAutomation,
    AppiumAutomation,
    PyAutoGUIAutomation,
    WalletAutomation,  # Backward compatibility alias
    Step,
    Annotation,
    create_automation,
)
from .annotation import AnnotationEngine
from .generator import DocumentationGenerator
from .config import WalletConfig

__all__ = [
    # Automation classes
    "BaseAutomation",
    "AppiumAutomation",
    "PyAutoGUIAutomation",
    "WalletAutomation",  # Backward compatibility
    "Step",
    "Annotation",
    "create_automation",
    # Other core modules
    "AnnotationEngine",
    "DocumentationGenerator",
    "WalletConfig",
]
