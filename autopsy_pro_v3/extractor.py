"""Enhanced code extraction with improved quality scoring, parallel processing, and semantic analysis"""
import re
import ast
import time
from pathlib import Path
from typing import List, Tuple, Set, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .models import Fragment, ExtractionResult, Project
from .config import Config
from .utils import safe_read_text, stable_uid

logger = logging.getLogger(__name__)


def compute_complexity(code: str, lang: str) -> int:
    """
    Compute cyclomatic complexity estimate
    """
    complexity = 1  # Base complexity

    # Decision points - separate keywords from operators
    python_keywords = ['if', 'elif', 'else', 'for', 'while', 'except']
    other_keywords = ['case', 'catch']
    operators = ['&&', '||', '?']

    if lang in ['py', 'python']:
        # Use word boundaries for Python keywords only
        for keyword in python_keywords:
            complexity += len(re.findall(rf'\b{re.escape(keyword)}\b', code))
        # Python uses 'and', 'or' instead of &&, ||
        complexity += len(re.findall(r'\b(and|or)\b', code))
    else:
        # For other languages, use word boundaries for keywords
        for keyword in python_keywords + other_keywords:
            complexity += len(re.findall(rf'\b{re.escape(keyword)}\b', code))
        # Count operators separately without word boundaries
        for operator in operators:
            complexity += code.count(operator)

    return complexity


def compute_documentation_ratio(code: str, lang: str) -> float:
    """
    Compute ratio of documentation to code
    """
    lines = code.splitlines()
    doc_lines = 0
    code_lines = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        code_lines += 1
        
        # Check for comments
        if lang in ['py', 'python']:
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                doc_lines += 1
        elif lang in ['js', 'javascript', 'typescript', 'go', 'rust', 'java', 'c', 'cpp']:
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                doc_lines += 1
        elif lang in ['ruby']:
            if stripped.startswith('#'):
                doc_lines += 1
        elif lang in ['php']:
            if stripped.startswith('//') or stripped.startswith('#') or stripped.startswith('/*'):
                doc_lines += 1
    
    return doc_lines / code_lines if code_lines > 0 else 0.0


def assess_quality_enhanced(code: str, lang: str, fragment_type: str) -> Tuple[int, Dict[str, any]]:
    """
    Enhanced quality assessment with detailed metrics
    Returns: (quality_score 1-10, metrics_dict)
    """
    lines = code.splitlines()
    text = code.lower()
    score = 5  # Start neutral
    metrics = {}
    
    # Line count scoring
    line_count = len([l for l in lines if l.strip()])
    metrics['line_count'] = line_count
    
    if 10 <= line_count <= 50:
        score += 2
        metrics['length_score'] = 2
    elif 5 <= line_count < 10 or 50 < line_count <= 100:
        score += 1
        metrics['length_score'] = 1
    elif line_count > 200:
        score -= 2
        metrics['length_score'] = -2
    else:
        metrics['length_score'] = 0
    
    # Documentation ratio
    doc_ratio = compute_documentation_ratio(code, lang)
    metrics['doc_ratio'] = doc_ratio
    
    if doc_ratio > 0.15:
        score += 2
    elif doc_ratio > 0.05:
        score += 1
    
    # Type hints (Python)
    if lang in ['py', 'python']:
        has_types = '->' in code or ': ' in code
        metrics['has_types'] = has_types
        if has_types:
            score += 1
    
    # TypeScript/typed code
    if lang in ['typescript', 'ts']:
        has_types = ': ' in code or 'interface' in text or 'type ' in text
        metrics['has_types'] = has_types
        if has_types:
            score += 1
    
    # Async patterns
    if 'async' in text or 'await' in text:
        score += 1
        metrics['has_async'] = True
    
    # Error handling
    has_error_handling = any(kw in text for kw in ['try', 'catch', 'except', 'error', 'throw'])
    metrics['has_error_handling'] = has_error_handling
    if has_error_handling:
        score += 1
    
    # Export declarations (good for reusability)
    if 'export' in text:
        score += 1
        metrics['has_exports'] = True
    
    # Negative factors
    
    # TODO/FIXME markers
    has_todos = 'todo' in text or 'fixme' in text or 'hack' in text
    metrics['has_todos'] = has_todos
    if has_todos:
        score -= 1
    
    # Debug statements
    debug_patterns = ['console.log', 'print(', 'println', 'fmt.println', 'debugger']
    has_debug = any(pat in text for pat in debug_patterns)
    metrics['has_debug'] = has_debug
    if has_debug:
        score -= 1
    
    # Tests (depending on context, might be positive or filtered separately)
    is_test = 'test' in text or 'spec' in text or 'describe' in text
    metrics['is_test'] = is_test
    if is_test and 'test' in fragment_type.lower():
        score += 1  # Good if we're looking for tests
    
    # Complexity
    complexity = compute_complexity(code, lang)
    metrics['complexity'] = complexity
    
    if complexity > 15:
        score -= 2
    elif complexity > 10:
        score -= 1
    elif 3 <= complexity <= 8:
        score += 1
    
    # Nesting depth
    max_indent = 0
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
    
    metrics['max_indent'] = max_indent
    if max_indent > 24:
        score -= 2
    elif max_indent > 16:
        score -= 1
    
    # Code smells
    if code.count('if') > 10:
        score -= 1
        metrics['too_many_ifs'] = True
    
    final_score = max(1, min(10, score))
    metrics['final_score'] = final_score
    
    return final_score, metrics


def extract_python_fragments(code: str, file_path: Path, project_name: str, config: Config) -> List[Fragment]:
    """Extract Python functions and classes using AST"""
    fragments = []
    
    try:
        tree = ast.parse(code)
        lines = code.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                # Get block
                start = getattr(node, "lineno", 1) - 1
                end = getattr(node, "end_lineno", start + 1)
                
                if 0 <= start < len(lines) and end <= len(lines):
                    block_lines = lines[start:end]
                    block = "\n".join(block_lines)
                    
                    # Skip if too short or too long
                    if len(block_lines) < config.min_lines or len(block_lines) > config.max_lines:
                        continue
                    
                    # Determine type
                    if isinstance(node, ast.ClassDef):
                        frag_type = "PythonClass"
                    elif isinstance(node, ast.AsyncFunctionDef):
                        frag_type = "PythonAsyncFunc"
                    else:
                        frag_type = "PythonFunc"
                    
                    # Extract imports (simple approach)
                    imports = []
                    for imp_node in ast.walk(node):
                        if isinstance(imp_node, ast.Import):
                            imports.extend([alias.name for alias in imp_node.names])
                        elif isinstance(imp_node, ast.ImportFrom):
                            if imp_node.module:
                                imports.append(imp_node.module)
                    
                    # Quality assessment
                    quality, metrics = assess_quality_enhanced(block, 'python', frag_type)
                    
                    # Skip low quality if configured
                    if quality < config.min_quality:
                        continue
                    
                    uid = stable_uid(project_name, file_path.name, str(start))
                    
                    fragment = Fragment(
                        uid=uid,
                        name=node.name,
                        type=frag_type,
                        file=str(file_path),
                        project=project_name,
                        code=block,
                        lines=len(block_lines),
                        quality=quality,
                        start_line=start + 1,
                        end_line=end,
                        imports=imports,
                        complexity=metrics.get('complexity', 0),
                        documentation_ratio=metrics.get('doc_ratio', 0.0),
                        has_types=metrics.get('has_types', False),
                        has_error_handling=metrics.get('has_error_handling', False),
                        has_tests=metrics.get('is_test', False)
                    )
                    
                    fragments.append(fragment)
    
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error extracting Python from {file_path}: {e}")
    
    return fragments


def extract_js_block(lines: List[str], start_line: int) -> Tuple[str, int]:
    """Extract JavaScript/TypeScript block with brace matching"""
    if start_line >= len(lines):
        return "", start_line
    
    line = lines[start_line]
    brace = 0
    seen_open = False
    
    for ch in line:
        if ch == "{":
            brace += 1
            seen_open = True
        elif ch == "}":
            brace -= 1
    
    if not seen_open:
        return line, start_line
    
    block = [line]
    end_line = start_line
    
    for i in range(start_line + 1, min(len(lines), start_line + 500)):  # Limit search
        end_line = i
        block.append(lines[i])
        
        for ch in lines[i]:
            if ch == "{":
                brace += 1
            elif ch == "}":
                brace -= 1
        
        if brace <= 0:
            break
    
    return "\n".join(block), end_line


def extract_js_fragments(code: str, file_path: Path, project_name: str, config: Config) -> List[Fragment]:
    """Extract JavaScript/TypeScript fragments"""
    fragments = []
    lines = code.splitlines()
    
    patterns = [
        (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", "Function"),
        (r"(?:export\s+)?class\s+(\w+)", "Class"),
        (r"const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", "ArrowFunc"),
        (r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>", "Component"),
    ]
    
    for pattern, frag_type in patterns:
        for match in re.finditer(pattern, code):
            name = match.group(1)
            start_line = code[:match.start()].count("\n")
            
            block, end_line = extract_js_block(lines, start_line)
            
            # Skip if too short or too long
            block_lines = block.splitlines()
            if len(block_lines) < config.min_lines or len(block_lines) > config.max_lines:
                continue
            
            # Quality assessment
            quality, metrics = assess_quality_enhanced(block, 'javascript', frag_type)
            
            if quality < config.min_quality:
                continue
            
            # Extract imports
            imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', block)
            
            # Check for exports
            exports = []
            if 'export' in block:
                exports.append(name)
            
            uid = stable_uid(project_name, file_path.name, str(start_line))
            
            fragment = Fragment(
                uid=uid,
                name=name,
                type=f"JS/{frag_type}",
                file=str(file_path),
                project=project_name,
                code=block,
                lines=len(block_lines),
                quality=quality,
                start_line=start_line + 1,
                end_line=end_line + 1,
                imports=imports,
                exports=exports,
                complexity=metrics.get('complexity', 0),
                documentation_ratio=metrics.get('doc_ratio', 0.0),
                has_types=metrics.get('has_types', False),
                has_error_handling=metrics.get('has_error_handling', False)
            )
            
            fragments.append(fragment)
    
    return fragments


def extract_from_file(file_path: Path, project: Project, config: Config) -> List[Fragment]:
    """Extract fragments from a single file"""
    try:
        code = safe_read_text(file_path)
        if not code:
            return []
        
        # Determine language and extract
        if file_path.suffix == '.py':
            return extract_python_fragments(code, file_path, project.name, config)
        elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
            return extract_js_fragments(code, file_path, project.name, config)
        # Add more languages as needed (Go, Rust, Java, etc.)
        
        return []
    
    except Exception as e:
        logger.error(f"Error extracting from {file_path}: {e}")
        return []


def deduplicate_fragments(fragments: List[Fragment]) -> List[Fragment]:
    """
    Remove duplicate fragments using both exact and semantic matching
    """
    seen_exact = set()
    seen_semantic = set()
    unique = []
    
    for frag in fragments:
        # Check exact match
        if frag.code_hash in seen_exact:
            logger.debug(f"Skipping exact duplicate: {frag.name}")
            continue
        
        # Compute semantic hash
        semantic_hash = frag.compute_embedding_hash()
        
        # Check semantic similarity (simple version)
        if semantic_hash in seen_semantic:
            logger.debug(f"Skipping semantic duplicate: {frag.name}")
            continue
        
        seen_exact.add(frag.code_hash)
        seen_semantic.add(semantic_hash)
        unique.append(frag)
    
    logger.info(f"Deduplicated: {len(fragments)} -> {len(unique)} fragments")
    return unique


def extract_fragments_parallel(projects: List[Project], config: Config) -> List[Fragment]:
    """
    Extract fragments from projects using parallel processing
    """
    all_fragments = []
    total_files = sum(len(p.code_files) for p in projects)
    
    logger.info(f"Extracting fragments from {total_files} files across {len(projects)} projects")
    
    if config.parallel_scan and total_files > 10:
        # Parallel extraction
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            futures = []
            for project in projects:
                for file_path in project.code_files:
                    future = executor.submit(extract_from_file, Path(file_path), project, config)
                    futures.append(future)
            
            for future in as_completed(futures):
                try:
                    fragments = future.result()
                    all_fragments.extend(fragments)
                except Exception as e:
                    logger.error(f"Extraction error: {e}")
    else:
        # Sequential extraction
        for project in projects:
            for file_path in project.code_files:
                fragments = extract_from_file(Path(file_path), project, config)
                all_fragments.extend(fragments)
    
    logger.info(f"Extracted {len(all_fragments)} raw fragments")
    
    # Deduplicate if configured
    if config.deduplicate:
        all_fragments = deduplicate_fragments(all_fragments)
    
    # Filter tests if configured
    if config.skip_tests:
        original_count = len(all_fragments)
        all_fragments = [f for f in all_fragments if not f.has_tests]
        logger.info(f"Filtered out {original_count - len(all_fragments)} test fragments")
    
    return all_fragments


def extract_fragments(projects: List[Project], config: Config) -> ExtractionResult:
    """
    Main entry point for fragment extraction
    """
    start_time = time.time()
    
    fragments = extract_fragments_parallel(projects, config)
    
    # Sort by quality (highest first)
    fragments.sort(key=lambda f: (f.quality, f.lines), reverse=True)
    
    extraction_time = time.time() - start_time
    
    logger.info(f"Extraction complete: {len(fragments)} fragments in {extraction_time:.2f}s")
    logger.info(f"Average quality: {sum(f.quality for f in fragments) / len(fragments):.1f}" if fragments else "N/A")
    
    return ExtractionResult(
        fragments=fragments,
        extraction_time=extraction_time
    )
