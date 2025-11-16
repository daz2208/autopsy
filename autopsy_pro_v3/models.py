"""Enhanced data models with rich metadata and serialization"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class Project:
    """Project metadata"""
    name: str
    path: str
    type: str
    files: int
    size_bytes: int
    last_modified: float
    code_files: List[str]
    
    # Enhanced metadata
    dependencies: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    languages: Set[str] = field(default_factory=set)
    complexity_score: float = 0.0
    health_score: float = 0.0
    
    @property
    def size_mb(self) -> float:
        """Size in megabytes"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def last_modified_date(self) -> datetime:
        """Last modified as datetime"""
        return datetime.fromtimestamp(self.last_modified)
    
    @property
    def days_inactive(self) -> int:
        """Days since last modification"""
        return (datetime.now() - self.last_modified_date).days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['languages'] = list(self.languages)  # Convert set to list
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary"""
        if 'languages' in data and isinstance(data['languages'], list):
            data['languages'] = set(data['languages'])
        return cls(**data)


@dataclass
class Fragment:
    """Code fragment with enhanced metadata"""
    uid: str
    name: str
    type: str
    file: str
    project: str
    code: str
    lines: int
    quality: int
    start_line: int
    
    # Enhanced metadata
    end_line: int = 0
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    complexity: int = 0
    documentation_ratio: float = 0.0
    has_types: bool = False
    has_tests: bool = False
    has_error_handling: bool = False
    tags: List[str] = field(default_factory=list)
    
    # Semantic analysis
    embedding_hash: Optional[str] = None
    similar_fragments: List[str] = field(default_factory=list)
    
    @property
    def file_name(self) -> str:
        """Just the filename"""
        return Path(self.file).name
    
    @property
    def language(self) -> str:
        """Infer language from type"""
        type_lower = self.type.lower()
        if 'python' in type_lower:
            return 'Python'
        elif 'js' in type_lower or 'typescript' in type_lower or 'react' in type_lower:
            return 'JavaScript/TypeScript'
        elif 'go' in type_lower:
            return 'Go'
        elif 'rust' in type_lower:
            return 'Rust'
        elif 'java' in type_lower:
            return 'Java'
        elif 'ruby' in type_lower:
            return 'Ruby'
        elif 'php' in type_lower:
            return 'PHP'
        elif 'swift' in type_lower:
            return 'Swift'
        return 'Unknown'
    
    @property
    def code_hash(self) -> str:
        """Hash of the code for comparison"""
        return hashlib.md5(self.code.encode()).hexdigest()
    
    def compute_embedding_hash(self) -> str:
        """Compute a simple semantic hash (would use embeddings in production)"""
        # Normalize code for semantic comparison
        normalized = self.code.lower()
        normalized = ''.join(c if c.isalnum() else ' ' for c in normalized)
        words = normalized.split()
        word_set = sorted(set(words))
        semantic_text = ' '.join(word_set[:50])  # First 50 unique words
        self.embedding_hash = hashlib.md5(semantic_text.encode()).hexdigest()
        return self.embedding_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fragment':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ScanResult:
    """Result of a project scan"""
    base_path: str
    projects: List[Project]
    scan_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_files(self) -> int:
        return sum(p.files for p in self.projects)
    
    @property
    def total_code_files(self) -> int:
        return sum(len(p.code_files) for p in self.projects)
    
    @property
    def total_size_mb(self) -> float:
        return sum(p.size_mb for p in self.projects)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'base_path': self.base_path,
            'projects': [p.to_dict() for p in self.projects],
            'scan_time': self.scan_time,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanResult':
        """Create from dictionary"""
        return cls(
            base_path=data['base_path'],
            projects=[Project.from_dict(p) for p in data['projects']],
            scan_time=data['scan_time'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class ExtractionResult:
    """Result of fragment extraction"""
    fragments: List[Fragment]
    extraction_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_lines(self) -> int:
        return sum(f.lines for f in self.fragments)
    
    @property
    def avg_quality(self) -> float:
        if not self.fragments:
            return 0.0
        return sum(f.quality for f in self.fragments) / len(self.fragments)
    
    @property
    def languages(self) -> Set[str]:
        return {f.language for f in self.fragments}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'fragments': [f.to_dict() for f in self.fragments],
            'extraction_time': self.extraction_time,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionResult':
        """Create from dictionary"""
        return cls(
            fragments=[Fragment.from_dict(f) for f in data['fragments']],
            extraction_time=data['extraction_time'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class BuildResult:
    """Result of project build"""
    success: bool
    output_path: str
    fragments_used: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    build_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'output_path': self.output_path,
            'fragments_used': self.fragments_used,
            'errors': self.errors,
            'warnings': self.warnings,
            'build_time': self.build_time,
            'timestamp': self.timestamp.isoformat()
        }
