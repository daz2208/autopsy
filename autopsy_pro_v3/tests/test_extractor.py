"""Tests for the extractor module"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autopsy_pro_v3.extractor import (
    compute_complexity,
    compute_documentation_ratio,
    assess_quality_enhanced
)


def test_compute_complexity_python():
    """Test complexity calculation for Python code"""
    # Simple code with basic control flow
    code = """
def example():
    if x > 0:
        for i in range(10):
            if i % 2 == 0:
                print(i)
    """
    complexity = compute_complexity(code, 'python')
    # Should have: 1 (base) + 2 (if) + 1 (for) = 4+
    assert complexity >= 4, f"Expected complexity >= 4, got {complexity}"


def test_compute_complexity_javascript():
    """Test complexity calculation for JavaScript code"""
    code = """
function example() {
    if (x > 0 && y < 10) {
        for (let i = 0; i < 10; i++) {
            if (i % 2 === 0) {
                console.log(i);
            }
        }
    }
}
    """
    complexity = compute_complexity(code, 'javascript')
    # Should count if, for, && operators
    assert complexity >= 4, f"Expected complexity >= 4, got {complexity}"


def test_compute_complexity_operators():
    """Test that special regex characters don't cause errors"""
    code = """
if (x > 0 && y < 10 || z == 5) {
    result = condition ? true : false;
}
    """
    # This should NOT raise a regex error
    try:
        complexity = compute_complexity(code, 'javascript')
        assert complexity > 1, "Complexity should be greater than base"
    except Exception as e:
        raise AssertionError(f"compute_complexity raised error with operators: {e}")


def test_compute_documentation_ratio_python():
    """Test documentation ratio for Python"""
    code = """
# This is a comment
def example():
    '''This is a docstring'''
    # Another comment
    x = 5
    return x
    """
    ratio = compute_documentation_ratio(code, 'python')
    assert 0.3 < ratio < 0.6, f"Expected ratio between 0.3 and 0.6, got {ratio}"


def test_compute_documentation_ratio_javascript():
    """Test documentation ratio for JavaScript"""
    code = """
// This is a comment
function example() {
    /* Multi-line
       comment */
    // Another comment
    const x = 5;
    return x;
}
    """
    ratio = compute_documentation_ratio(code, 'javascript')
    assert 0.2 < ratio < 0.5, f"Expected ratio between 0.2 and 0.5, got {ratio}"


def test_assess_quality_enhanced_good_code():
    """Test quality assessment for good code"""
    code = """
def process_data(items: list, threshold: int) -> dict:
    '''
    Process items and return summary statistics.

    Args:
        items: List of items to process
        threshold: Minimum value threshold

    Returns:
        Dictionary with statistics
    '''
    try:
        result = {}
        valid_items = [x for x in items if x > threshold]

        result['count'] = len(valid_items)
        result['total'] = sum(valid_items)

        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return {}
    """
    score, metrics = assess_quality_enhanced(code, 'python', 'PythonFunc')

    # Should have high score due to:
    # - Good length (10-50 lines)
    # - Documentation
    # - Type hints
    # - Error handling
    assert score >= 7, f"Expected score >= 7 for good code, got {score}"
    assert metrics['has_types'] == True, "Should detect type hints"
    assert metrics['has_error_handling'] == True, "Should detect error handling"


def test_assess_quality_enhanced_poor_code():
    """Test quality assessment for poor code"""
    code = """
def x():
    # TODO: fix this hack
    print("debug")
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            print("too deep")
    """
    score, metrics = assess_quality_enhanced(code, 'python', 'PythonFunc')

    # Should have lower score due to:
    # - TODO marker
    # - Debug print
    # - Deep nesting
    assert score < 7, f"Expected score < 7 for poor code, got {score}"
    assert metrics['has_todos'] == True, "Should detect TODO"
    assert metrics['has_debug'] == True, "Should detect debug statement"


def test_assess_quality_enhanced_no_crash():
    """Test that quality assessment doesn't crash on edge cases"""
    test_cases = [
        "",  # Empty string
        "x = 5",  # Single line
        "\n\n\n",  # Only whitespace
        "# Just a comment",  # Only comment
    ]

    for code in test_cases:
        try:
            score, metrics = assess_quality_enhanced(code, 'python', 'PythonFunc')
            assert 1 <= score <= 10, f"Score should be 1-10, got {score}"
        except Exception as e:
            raise AssertionError(f"assess_quality_enhanced crashed on '{code}': {e}")


if __name__ == '__main__':
    print("Running extractor tests...")

    tests = [
        test_compute_complexity_python,
        test_compute_complexity_javascript,
        test_compute_complexity_operators,
        test_compute_documentation_ratio_python,
        test_compute_documentation_ratio_javascript,
        test_assess_quality_enhanced_good_code,
        test_assess_quality_enhanced_poor_code,
        test_assess_quality_enhanced_no_crash,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
