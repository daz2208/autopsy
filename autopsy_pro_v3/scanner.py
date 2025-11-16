"""Enhanced project scanner with parallel processing, caching, and better detection"""
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .models import Project, ScanResult
from .config import Config, get_cache_path

logger = logging.getLogger(__name__)


PROJECT_INDICATORS = {
    "package.json": ("Node.js", ["node", "npm", "yarn"]),
    "requirements.txt": ("Python", ["pip"]),
    "pyproject.toml": ("Python", ["poetry", "pip"]),
    "Pipfile": ("Python", ["pipenv"]),
    "Cargo.toml": ("Rust", ["cargo"]),
    "pom.xml": ("Java Maven", ["maven"]),
    "build.gradle": ("Java Gradle", ["gradle"]),
    "build.gradle.kts": ("Kotlin Gradle", ["gradle", "kotlin"]),
    "go.mod": ("Go", ["go"]),
    "composer.json": ("PHP", ["composer"]),
    ".git": ("Git Repository", []),
    "manage.py": ("Django", ["django", "python"]),
    "setup.py": ("Python Package", ["setuptools"]),
    "Makefile": ("Make Project", ["make"]),
    "CMakeLists.txt": ("CMake Project", ["cmake"]),
    "tsconfig.json": ("TypeScript", ["typescript", "tsc"]),
    "next.config.js": ("Next.js", ["next", "react"]),
    "next.config.mjs": ("Next.js", ["next", "react"]),
    "nuxt.config.js": ("Nuxt.js", ["nuxt", "vue"]),
    "vue.config.js": ("Vue.js", ["vue"]),
    "angular.json": ("Angular", ["angular"]),
    "pubspec.yaml": ("Flutter/Dart", ["flutter", "dart"]),
    "Gemfile": ("Ruby", ["bundler", "ruby"]),
    "mix.exs": ("Elixir", ["mix", "elixir"]),
    "stack.yaml": ("Haskell Stack", ["stack"]),
    "deno.json": ("Deno", ["deno"]),
    "app.config.ts": ("React Native", ["react-native"]),
}


def detect_project_info(files: List[str], path: Path) -> Tuple[str, List[str], List[str]]:
    """
    Detect project type, frameworks, and dependencies
    Returns: (project_type, frameworks, dependencies)
    """
    project_type = "Unknown"
    frameworks = []
    dependencies = []
    
    # Check indicator files
    for file in files:
        if file in PROJECT_INDICATORS:
            detected_type, deps = PROJECT_INDICATORS[file]
            if project_type == "Unknown":
                project_type = detected_type
            frameworks.append(detected_type)
            dependencies.extend(deps)
    
    # Parse package.json for more details
    if "package.json" in files:
        try:
            pkg_file = path / "package.json"
            with open(pkg_file, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                deps = pkg.get('dependencies', {})
                dev_deps = pkg.get('devDependencies', {})
                
                # Detect frameworks
                if 'react' in deps or 'react' in dev_deps:
                    frameworks.append('React')
                if 'vue' in deps:
                    frameworks.append('Vue')
                if 'express' in deps:
                    frameworks.append('Express')
                if 'fastify' in deps:
                    frameworks.append('Fastify')
                if '@nestjs/core' in deps:
                    frameworks.append('NestJS')
                
                # Add dependencies
                dependencies.extend(list(deps.keys())[:10])  # First 10 deps
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
    
    # Fallback detection based on file extensions
    if project_type == "Unknown":
        extensions = {f.split('.')[-1] for f in files if '.' in f}
        
        ext_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'jsx': 'React',
            'tsx': 'React TypeScript',
            'go': 'Go',
            'rs': 'Rust',
            'java': 'Java',
            'rb': 'Ruby',
            'php': 'PHP',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'c': 'C',
            'cpp': 'C++',
            'cs': 'C#',
        }
        
        for ext, lang in ext_map.items():
            if ext in extensions:
                project_type = lang
                break
    
    return project_type, list(set(frameworks)), list(set(dependencies))


def is_project_root(path: Path, files: List[str]) -> bool:
    """Determine if directory is a project root"""
    # Check for common project indicators
    indicators = set(PROJECT_INDICATORS.keys())
    
    if any(f in indicators for f in files):
        return True
    
    # Check for common project structure
    dir_name = path.name.lower()
    
    # Common project patterns
    project_patterns = ['project', 'app', 'service', 'api', 'web', 'backend', 'frontend', 'server']
    if any(pattern in dir_name for pattern in project_patterns):
        try:
            subdirs = [d for d in path.iterdir() if d.is_dir()]
            subdir_names = {d.name.lower() for d in subdirs}
            
            # Check for source directories
            src_indicators = ['src', 'lib', 'source', 'app', 'components', 'pages', 'api', 'handlers']
            if any(name in subdir_names for name in src_indicators):
                return True
        except PermissionError:
            pass
    
    return False


def scan_directory(root_path: Path, config: Config) -> Optional[Project]:
    """
    Scan a single directory and return Project if it's a valid project
    """
    try:
        files = os.listdir(root_path)
    except (PermissionError, OSError) as e:
        logger.debug(f"Cannot access {root_path}: {e}")
        return None
    
    # Check if it's a project root
    if not is_project_root(root_path, files):
        return None
    
    logger.info(f"Scanning project: {root_path}")
    
    try:
        code_files = []
        all_files = []
        total_size = 0
        latest_mod = 0
        languages = set()
        
        max_size = int(config.max_file_mb * 1024 * 1024)
        
        # Walk the project directory
        for root, dirs, dir_files in os.walk(root_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in config.ignore and not d.startswith('.')]
            
            for file in dir_files:
                file_path = Path(root) / file
                
                try:
                    if not file_path.exists():
                        continue
                    
                    stat = file_path.stat()
                    total_size += stat.st_size
                    all_files.append(file)
                    
                    # Check if it's a code file
                    for ext in config.exts:
                        if file.endswith(ext):
                            if stat.st_size <= max_size:
                                code_files.append(str(file_path))
                                latest_mod = max(latest_mod, stat.st_mtime)
                                
                                # Track language
                                lang_ext = ext.lstrip('.')
                                if lang_ext in ['py']:
                                    languages.add('Python')
                                elif lang_ext in ['js', 'jsx', 'ts', 'tsx']:
                                    languages.add('JavaScript/TypeScript')
                                elif lang_ext == 'go':
                                    languages.add('Go')
                                elif lang_ext == 'rs':
                                    languages.add('Rust')
                                elif lang_ext == 'java':
                                    languages.add('Java')
                                elif lang_ext == 'rb':
                                    languages.add('Ruby')
                                elif lang_ext == 'php':
                                    languages.add('PHP')
                            break
                
                except (OSError, PermissionError):
                    continue
        
        # Skip if no code files found
        if not code_files:
            return None
        
        # Check activity threshold
        last_mod_date = datetime.fromtimestamp(latest_mod) if latest_mod > 0 else datetime.min
        cutoff_date = datetime.now() - timedelta(days=config.inactive_days)
        is_active = last_mod_date > cutoff_date
        
        if not config.include_active and is_active:
            logger.debug(f"Skipping active project: {root_path.name}")
            return None
        
        # Detect project info
        proj_type, frameworks, dependencies = detect_project_info(all_files, root_path)
        
        # Create project
        project = Project(
            name=root_path.name,
            path=str(root_path),
            type=proj_type,
            files=len(all_files),
            size_bytes=total_size,
            last_modified=latest_mod,
            code_files=code_files,
            dependencies=dependencies[:20],  # Limit to 20
            frameworks=frameworks,
            languages=languages
        )
        
        logger.info(f"Added project: {project.name} ({proj_type}) - {len(code_files)} code files")
        return project
    
    except Exception as e:
        logger.error(f"Error processing project {root_path}: {e}")
        return None


def scan_projects_parallel(base: Path, config: Config) -> List[Project]:
    """
    Enhanced parallel project scanner
    """
    start_time = time.time()
    project_roots = []
    
    logger.info(f"Scanning {base} for projects...")
    logger.info(f"Extensions: {config.exts}")
    logger.info(f"Ignored: {config.ignore}")
    logger.info(f"Inactive threshold: {config.inactive_days} days")
    
    # First pass: identify potential project roots
    try:
        for root, dirs, files in os.walk(base):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in config.ignore and not d.startswith('.')]
            
            root_path = Path(root)
            
            # Skip if we're already inside a detected project
            skip = False
            for pr in project_roots:
                try:
                    if root_path.is_relative_to(pr) and root_path != pr:
                        skip = True
                        break
                except ValueError:
                    continue
            
            if skip:
                continue
            
            # Check if this is a project root
            if is_project_root(root_path, files):
                project_roots.append(root_path)
                # Don't descend into detected projects
                dirs.clear()
    except Exception as e:
        logger.error(f"Error during directory walk: {e}")
        return []
    
    logger.info(f"Found {len(project_roots)} potential project roots")
    
    # Second pass: process projects in parallel
    projects = []
    
    if config.parallel_scan and len(project_roots) > 1:
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            future_to_path = {
                executor.submit(scan_directory, path, config): path
                for path in project_roots
            }
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    project = future.result()
                    if project:
                        projects.append(project)
                except Exception as e:
                    logger.error(f"Error scanning {path}: {e}")
    else:
        # Sequential scanning
        for path in project_roots:
            project = scan_directory(path, config)
            if project:
                projects.append(project)
    
    scan_time = time.time() - start_time
    logger.info(f"Scan complete: Found {len(projects)} projects in {scan_time:.2f}s")
    
    # Sort by last modified (most recent first)
    projects.sort(key=lambda p: p.last_modified, reverse=True)
    
    return projects


def scan_projects(base: Path, config: Config, use_cache: bool = True) -> ScanResult:
    """
    Main entry point for project scanning with optional caching
    """
    cache_key = f"scan_{base}_{config.inactive_days}_{config.include_active}"
    cache_file = get_cache_path(cache_key)
    
    # Try to load from cache
    if use_cache and config.enable_cache and cache_file.exists():
        try:
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < config.cache_ttl_hours * 3600:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                result = ScanResult.from_dict(data)
                logger.info(f"Loaded scan results from cache ({len(result.projects)} projects)")
                return result
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
    
    # Perform scan
    start_time = time.time()
    projects = scan_projects_parallel(base, config)
    scan_time = time.time() - start_time
    
    result = ScanResult(
        base_path=str(base),
        projects=projects,
        scan_time=scan_time
    )
    
    # Save to cache
    if config.enable_cache:
        try:
            with open(cache_file, 'w') as f:
                json.dump(result.to_dict(), f)
            logger.info("Scan results cached")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    return result
