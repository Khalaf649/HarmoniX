# models/__init__.py
"""
AI Models package for Signal Equalizer
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Now import
from integration_api import AIModelsAPI
from model_manager import ModelManager
from performance import PerformanceComparator

__all__ = ['AIModelsAPI', 'ModelManager', 'PerformanceComparator']
__version__ = '1.0.0'