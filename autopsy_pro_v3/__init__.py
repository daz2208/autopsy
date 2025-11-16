"""
Autopsy Pro v3 - Enhanced Code Extraction and Project Rebuilding Tool

Extract high-quality code fragments from inactive projects and rebuild them
into new, organized projects.
"""

__version__ = "3.0.0"
__author__ = "Autopsy Pro Team"

from .models import Project, Fragment, ScanResult, ExtractionResult, BuildResult
from .config import Config, load_config, save_config
from .scanner import scan_projects
from .extractor import extract_fragments

__all__ = [
    'Project',
    'Fragment',
    'ScanResult',
    'ExtractionResult',
    'BuildResult',
    'Config',
    'load_config',
    'save_config',
    'scan_projects',
    'extract_fragments',
]
