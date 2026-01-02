"""
Orion - Personal Cognitive Augmentation Assistant
Core initialization
"""

__version__ = "0.1.0-mvp"
__author__ = "Orion"

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
