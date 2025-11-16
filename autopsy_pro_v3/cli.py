"""Command-line interface for Autopsy Pro"""
import argparse
import sys
import json
from pathlib import Path
from typing import List
import logging

from .config import load_config, save_config, Config, get_export_path, clear_cache
from .scanner import scan_projects
from .extractor import extract_fragments
from .models import Fragment, Project

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_scan(args):
    """Scan for projects"""
    config = load_config()
    
    # Override config with CLI args
    if args.inactive_days is not None:
        config.inactive_days = args.inactive_days
    if args.include_active:
        config.include_active = True
    if args.extensions:
        config.exts = args.extensions.split(',')
    
    base_path = Path(args.directory).expanduser().resolve()
    
    if not base_path.exists():
        print(f"Error: Directory not found: {base_path}")
        return 1
    
    print(f"Scanning {base_path}...")
    result = scan_projects(base_path, config, use_cache=not args.no_cache)
    
    print(f"\nScan Results:")
    print(f"  Projects found: {len(result.projects)}")
    print(f"  Total files: {result.total_files:,}")
    print(f"  Code files: {result.total_code_files:,}")
    print(f"  Total size: {result.total_size_mb:.1f} MB")
    print(f"  Scan time: {result.scan_time:.2f}s")
    
    if args.verbose:
        print(f"\nProjects:")
        for i, p in enumerate(result.projects[:20], 1):
            print(f"  {i}. {p.name} ({p.type}) - {len(p.code_files)} files, {p.days_inactive} days old")
    
    # Save if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nResults saved to: {output_path}")
    
    return 0


def cmd_extract(args):
    """Extract code fragments"""
    config = load_config()
    
    # Override config
    if args.min_quality is not None:
        config.min_quality = args.min_quality
    if args.skip_tests:
        config.skip_tests = True
    if args.no_dedupe:
        config.deduplicate = False
    
    # Load projects
    if args.scan_file:
        scan_file = Path(args.scan_file)
        if not scan_file.exists():
            print(f"Error: Scan file not found: {scan_file}")
            return 1
        
        with open(scan_file, 'r') as f:
            scan_data = json.load(f)
        
        from .models import ScanResult
        scan_result = ScanResult.from_dict(scan_data)
        projects = scan_result.projects
    else:
        # Need to scan first
        base_path = Path(args.directory).expanduser().resolve()
        print(f"Scanning {base_path}...")
        scan_result = scan_projects(base_path, config)
        projects = scan_result.projects
        print(f"Found {len(projects)} projects")
    
    print(f"Extracting fragments...")
    result = extract_fragments(projects, config)
    
    print(f"\nExtraction Results:")
    print(f"  Fragments extracted: {len(result.fragments)}")
    print(f"  Total lines: {result.total_lines:,}")
    print(f"  Average quality: {result.avg_quality:.1f}/10")
    print(f"  Languages: {', '.join(sorted(result.languages))}")
    print(f"  Extraction time: {result.extraction_time:.2f}s")
    
    if args.verbose:
        # Show top fragments
        print(f"\nTop 20 fragments by quality:")
        for i, f in enumerate(result.fragments[:20], 1):
            print(f"  {i}. {f.name} ({f.type}) - Quality: {f.quality}/10, Lines: {f.lines}")
    
    # Save if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nResults saved to: {output_path}")
    
    return 0


def cmd_export(args):
    """Export fragment collection"""
    # Load fragments
    if not args.fragments_file:
        print("Error: --fragments-file required for export")
        return 1
    
    fragments_file = Path(args.fragments_file)
    if not fragments_file.exists():
        print(f"Error: Fragments file not found: {fragments_file}")
        return 1
    
    with open(fragments_file, 'r') as f:
        data = json.load(f)
    
    from .models import ExtractionResult
    result = ExtractionResult.from_dict(data)
    
    # Filter if requested
    fragments = result.fragments
    if args.min_quality:
        fragments = [f for f in fragments if f.quality >= args.min_quality]
    if args.language:
        fragments = [f for f in fragments if args.language.lower() in f.language.lower()]
    
    print(f"Exporting {len(fragments)} fragments...")
    
    # Create export
    export_data = {
        'name': args.name or 'export',
        'description': args.description or 'Exported fragment collection',
        'fragments': [f.to_dict() for f in fragments],
        'metadata': {
            'total': len(fragments),
            'avg_quality': sum(f.quality for f in fragments) / len(fragments) if fragments else 0,
            'languages': list({f.language for f in fragments})
        }
    }
    
    # Save
    export_path = get_export_path(args.name or 'export')
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Export saved to: {export_path}")
    return 0


def cmd_import(args):
    """Import fragment collection"""
    import_file = Path(args.file)
    if not import_file.exists():
        print(f"Error: Import file not found: {import_file}")
        return 1
    
    with open(import_file, 'r') as f:
        data = json.load(f)
    
    print(f"Import: {data.get('name', 'Unknown')}")
    print(f"Description: {data.get('description', 'N/A')}")
    
    metadata = data.get('metadata', {})
    print(f"\nMetadata:")
    print(f"  Fragments: {metadata.get('total', 0)}")
    print(f"  Avg Quality: {metadata.get('avg_quality', 0):.1f}/10")
    print(f"  Languages: {', '.join(metadata.get('languages', []))}")
    
    if args.verbose and 'fragments' in data:
        print(f"\nFragments:")
        for i, frag_data in enumerate(data['fragments'][:20], 1):
            print(f"  {i}. {frag_data['name']} ({frag_data['type']}) - Quality: {frag_data['quality']}/10")
    
    return 0


def cmd_config(args):
    """Manage configuration"""
    if args.show:
        config = load_config()
        print("Current Configuration:")
        print(json.dumps(config.to_dict(), indent=2))
    elif args.reset:
        config = Config()
        save_config(config)
        print("Configuration reset to defaults")
    elif args.set:
        config = load_config()
        key, value = args.set.split('=', 1)
        
        # Parse value
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif '.' in value and value.replace('.', '').isdigit():
            value = float(value)
        
        # Set value
        if hasattr(config, key):
            setattr(config, key, value)
            if save_config(config):
                print(f"Set {key} = {value}")
            else:
                print(f"Error: Could not save configuration")
                return 1
        else:
            print(f"Error: Unknown config key: {key}")
            return 1
    
    return 0


def cmd_cache(args):
    """Manage cache"""
    if args.clear:
        clear_cache()
        print("Cache cleared")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Autopsy Pro - Extract and rebuild code from inactive projects'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan for projects')
    scan_parser.add_argument('directory', help='Directory to scan')
    scan_parser.add_argument('--inactive-days', type=int, help='Days of inactivity threshold')
    scan_parser.add_argument('--include-active', action='store_true', help='Include active projects')
    scan_parser.add_argument('--extensions', help='Comma-separated file extensions')
    scan_parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    scan_parser.add_argument('-o', '--output', help='Save results to file')
    scan_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract code fragments')
    extract_parser.add_argument('--directory', help='Directory to scan (if no scan file)')
    extract_parser.add_argument('--scan-file', help='Use existing scan results')
    extract_parser.add_argument('--min-quality', type=int, help='Minimum quality score')
    extract_parser.add_argument('--skip-tests', action='store_true', help='Skip test fragments')
    extract_parser.add_argument('--no-dedupe', action='store_true', help='Disable deduplication')
    extract_parser.add_argument('-o', '--output', help='Save results to file')
    extract_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export fragment collection')
    export_parser.add_argument('--fragments-file', required=True, help='Fragments JSON file')
    export_parser.add_argument('--name', help='Export name')
    export_parser.add_argument('--description', help='Export description')
    export_parser.add_argument('--min-quality', type=int, help='Filter by minimum quality')
    export_parser.add_argument('--language', help='Filter by language')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import fragment collection')
    import_parser.add_argument('file', help='Import file')
    import_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current config')
    config_parser.add_argument('--reset', action='store_true', help='Reset to defaults')
    config_parser.add_argument('--set', help='Set config value (key=value)')
    
    # Cache command
    cache_parser = subparsers.add_parser('cache', help='Manage cache')
    cache_parser.add_argument('--clear', action='store_true', help='Clear cache')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    handlers = {
        'scan': cmd_scan,
        'extract': cmd_extract,
        'export': cmd_export,
        'import': cmd_import,
        'config': cmd_config,
        'cache': cmd_cache,
    }
    
    try:
        return handlers[args.command](args)
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        logger.exception("Error executing command")
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
