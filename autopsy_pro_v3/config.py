"""Enhanced configuration management with validation and defaults"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".autopsy_pro"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"
EXPORT_DIR = CONFIG_DIR / "exports"


@dataclass
class Config:
    """Configuration data class with defaults"""
    # Scanning
    exts: List[str] = None
    ignore: List[str] = None
    inactive_days: int = 60
    include_active: bool = False
    max_file_mb: float = 1.0
    
    # Extraction
    min_quality: int = 5
    min_lines: int = 5
    max_lines: int = 500
    skip_tests: bool = False
    deduplicate: bool = True
    
    # Building
    organize_by_type: bool = True
    create_readme: bool = True
    create_tests: bool = False
    include_deps: bool = True
    
    # UI
    dark_mode: bool = False
    auto_save: bool = True
    
    # Performance
    parallel_scan: bool = True
    max_workers: int = 4
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    
    def __post_init__(self):
        """Set defaults for None values"""
        if self.exts is None:
            self.exts = [
                ".py", ".js", ".jsx", ".ts", ".tsx",
                ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
                ".rb", ".php", ".swift", ".kt", ".scala"
            ]
        if self.ignore is None:
            self.ignore = [
                ".git", "node_modules", "__pycache__", "venv", ".venv",
                "env", "build", "dist", ".idea", ".vscode", "target",
                "vendor", ".next", ".nuxt", "coverage"
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
    
    def validate(self) -> List[str]:
        """Validate configuration, return list of issues"""
        issues = []
        
        if self.inactive_days < 0:
            issues.append("inactive_days must be >= 0")
        if self.max_file_mb <= 0:
            issues.append("max_file_mb must be > 0")
        if not 1 <= self.min_quality <= 10:
            issues.append("min_quality must be between 1-10")
        if self.min_lines < 1:
            issues.append("min_lines must be >= 1")
        if self.max_lines < self.min_lines:
            issues.append("max_lines must be >= min_lines")
        if self.max_workers < 1:
            issues.append("max_workers must be >= 1")
        if self.cache_ttl_hours < 1:
            issues.append("cache_ttl_hours must be >= 1")
        
        return issues


def ensure_dirs():
    """Ensure required directories exist"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)


def load_config() -> Config:
    """Load configuration from file or create default"""
    ensure_dirs()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            config = Config.from_dict(data)
            
            # Validate
            issues = config.validate()
            if issues:
                logger.warning(f"Config validation issues: {issues}")
                logger.warning("Using defaults for invalid values")
                return Config()
            
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return Config()
    else:
        config = Config()
        save_config(config)
        return config


def save_config(config: Config) -> bool:
    """Save configuration to file"""
    ensure_dirs()
    
    # Validate before saving
    issues = config.validate()
    if issues:
        logger.error(f"Cannot save invalid config: {issues}")
        return False
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


def get_cache_path(key: str) -> Path:
    """Get cache file path for a key"""
    ensure_dirs()
    # Sanitize key for filename
    safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
    return CACHE_DIR / f"{safe_key}.json"


def get_export_path(name: str) -> Path:
    """Get export file path"""
    ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    return EXPORT_DIR / f"{safe_name}.json"


def clear_cache():
    """Clear all cached data"""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Error deleting cache file {cache_file}: {e}")
        logger.info("Cache cleared")
