"""
PyIDVerify Utilities Package
==========================

This package provides essential utility functions for ID validation including:
- Mathematical algorithms (Luhn, Verhoeff, Damm, MOD-97)
- Formatting and masking utilities
- Secure test data generation
- Data extraction and parsing
- Performance optimization utilities

The utilities are designed with security-first principles and optimized
for high-performance validation operations.

Examples:
    >>> from pyidverify.utils import luhn_check, format_credit_card, mask_sensitive_data
    >>> 
    >>> # Validate credit card using Luhn algorithm
    >>> is_valid = luhn_check("4532015112830366")
    >>> 
    >>> # Format credit card for display
    >>> formatted = format_credit_card("4532015112830366")
    >>> # Returns: "4532-0151-1283-0366"
    >>> 
    >>> # Mask sensitive data
    >>> masked = mask_sensitive_data("4532015112830366", mask_char="*", visible_start=4, visible_end=4)
    >>> # Returns: "4532********0366"

Security Features:
- Constant-time algorithms to prevent timing attacks
- Secure random number generation for test data
- Memory clearing for sensitive operations
- Input sanitization and validation
"""

from typing import Dict, Any, List, Optional, Union, Callable
import sys
from pathlib import Path

# Version information
__version__ = "0.1.0-dev"
__author__ = "PyIDVerify Team"
__license__ = "MIT"

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import core utility functions
try:
    from .algorithms import (
        luhn_check,
        luhn_calculate_check_digit,
        verhoeff_check,
        verhoeff_calculate_check_digit,
        damm_check,
        damm_calculate_check_digit,
        mod97_check,
        mod97_calculate_check_digits,
        isbn_check,
        issn_check,
        Algorithm,
        AlgorithmResult
    )
    
    from .formatters import (
        format_credit_card,
        format_phone_number,
        format_ssn,
        format_iban,
        mask_sensitive_data,
        progressive_disclosure,
        international_format,
        FormattingStyle,
        MaskingOptions,
        FormatResult
    )
    
    from .generators import (
        generate_test_credit_card,
        generate_test_ssn,
        generate_test_phone,
        generate_test_email,
        generate_invalid_data,
        generate_edge_cases,
        TestDataType,
        GenerationOptions,
        TestDataResult
    )
    
    from .extractors import (
        extract_numbers,
        extract_patterns,
        normalize_input,
        clean_input,
        parse_structured_data,
        ExtractionResult,
        ParsingOptions
    )
    
    from .caching import (
        LRUCache,
        TTLCache,
        SecureCache,
        CacheStats,
        cache_result,
        clear_cache
    )
    
    _IMPORTS_SUCCESSFUL = True
    
except ImportError as e:
    # Graceful degradation if some modules aren't available
    _IMPORTS_SUCCESSFUL = False
    _IMPORT_ERROR = str(e)
    
    # Define minimal fallback functions
    def luhn_check(number: str) -> bool:
        """Fallback Luhn check implementation"""
        raise ImportError(f"Algorithm utilities not available: {_IMPORT_ERROR}")
    
    def format_credit_card(number: str) -> str:
        """Fallback credit card formatting"""
        raise ImportError(f"Formatting utilities not available: {_IMPORT_ERROR}")

# Utility constants
ALGORITHMS = [
    "luhn",
    "verhoeff", 
    "damm",
    "mod97",
    "isbn",
    "issn"
]

SUPPORTED_FORMATS = [
    "credit_card",
    "phone_number", 
    "ssn",
    "iban",
    "custom"
]

MASKING_STYLES = [
    "partial",
    "progressive",
    "tokenized",
    "hashed"
]

# Performance optimization settings
DEFAULT_CACHE_SIZE = 1000
DEFAULT_CACHE_TTL = 3600  # 1 hour
MAX_BATCH_SIZE = 10000

def get_available_algorithms() -> List[str]:
    """
    Get list of available mathematical algorithms.
    
    Returns:
        List of algorithm names that can be used for validation
        
    Example:
        >>> algorithms = get_available_algorithms()
        >>> print(algorithms)
        ['luhn', 'verhoeff', 'damm', 'mod97', 'isbn', 'issn']
    """
    if not _IMPORTS_SUCCESSFUL:
        return []
    return ALGORITHMS.copy()

def get_supported_formats() -> List[str]:
    """
    Get list of supported formatting types.
    
    Returns:
        List of format types that can be applied to ID values
        
    Example:
        >>> formats = get_supported_formats()
        >>> print(formats)
        ['credit_card', 'phone_number', 'ssn', 'iban', 'custom']
    """
    if not _IMPORTS_SUCCESSFUL:
        return []
    return SUPPORTED_FORMATS.copy()

def validate_algorithm_input(value: str, algorithm: str) -> bool:
    """
    Validate input for mathematical algorithms.
    
    Args:
        value: Input value to validate
        algorithm: Algorithm name to use
        
    Returns:
        True if input is valid for the algorithm
        
    Raises:
        ValueError: If algorithm is not supported
        TypeError: If input is not a string
        
    Example:
        >>> is_valid = validate_algorithm_input("123456", "luhn")
        >>> print(is_valid)
        True
    """
    if not isinstance(value, str):
        raise TypeError("Input value must be a string")
    
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    if not value or not value.strip():
        return False
    
    # Remove common separators for algorithm validation
    cleaned_value = ''.join(c for c in value if c.isdigit())
    return len(cleaned_value) > 0

def benchmark_algorithm(algorithm: str, iterations: int = 10000) -> Dict[str, float]:
    """
    Benchmark performance of a mathematical algorithm.
    
    Args:
        algorithm: Algorithm name to benchmark
        iterations: Number of test iterations
        
    Returns:
        Dictionary containing performance metrics
        
    Example:
        >>> results = benchmark_algorithm("luhn", 1000)
        >>> print(f"Average time: {results['avg_time_ms']:.2f}ms")
    """
    if not _IMPORTS_SUCCESSFUL:
        raise ImportError(f"Benchmarking not available: {_IMPORT_ERROR}")
    
    import time
    import random
    
    # Generate test data
    test_numbers = []
    for _ in range(iterations):
        # Generate random 16-digit number for testing
        number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        test_numbers.append(number)
    
    # Get algorithm function
    algorithm_map = {
        "luhn": luhn_check,
        "verhoeff": verhoeff_check,
        "damm": damm_check,
        "mod97": mod97_check,
        "isbn": isbn_check,
        "issn": issn_check
    }
    
    if algorithm not in algorithm_map:
        raise ValueError(f"Algorithm not available for benchmarking: {algorithm}")
    
    func = algorithm_map[algorithm]
    
    # Run benchmark
    start_time = time.perf_counter()
    
    for number in test_numbers:
        try:
            func(number)
        except:
            pass  # Ignore validation errors during benchmarking
    
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    avg_time = total_time / iterations
    
    return {
        "algorithm": algorithm,
        "iterations": iterations,
        "total_time_s": total_time,
        "avg_time_ms": avg_time * 1000,
        "operations_per_second": iterations / total_time if total_time > 0 else 0
    }

def create_custom_formatter(pattern: str, separator: str = "-") -> Callable[[str], str]:
    """
    Create a custom formatter function based on a pattern.
    
    Args:
        pattern: Format pattern using 'X' for digits (e.g., "XXXX-XXXX-XXXX-XXXX")
        separator: Character to use as separator
        
    Returns:
        Custom formatting function
        
    Example:
        >>> formatter = create_custom_formatter("XXXX-XXXX-XXXX-XXXX")
        >>> formatted = formatter("1234567890123456")
        >>> print(formatted)
        1234-5678-9012-3456
    """
    if not _IMPORTS_SUCCESSFUL:
        raise ImportError(f"Custom formatting not available: {_IMPORT_ERROR}")
    
    def custom_format(value: str) -> str:
        """Apply custom formatting pattern to input value"""
        if not value:
            return value
        
        # Clean input - keep only digits
        digits = ''.join(c for c in value if c.isdigit())
        
        # Apply pattern
        result = []
        digit_index = 0
        
        for char in pattern:
            if char == 'X':
                if digit_index < len(digits):
                    result.append(digits[digit_index])
                    digit_index += 1
                else:
                    break
            else:
                result.append(char)
        
        return ''.join(result)
    
    return custom_format

def get_utility_info() -> Dict[str, Any]:
    """
    Get information about available utility functions.
    
    Returns:
        Dictionary containing utility package information
        
    Example:
        >>> info = get_utility_info()
        >>> print(f"Algorithms available: {info['algorithms_count']}")
    """
    return {
        "version": __version__,
        "imports_successful": _IMPORTS_SUCCESSFUL,
        "import_error": _IMPORT_ERROR if not _IMPORTS_SUCCESSFUL else None,
        "algorithms_available": len(ALGORITHMS) if _IMPORTS_SUCCESSFUL else 0,
        "algorithms": ALGORITHMS if _IMPORTS_SUCCESSFUL else [],
        "formats_available": len(SUPPORTED_FORMATS) if _IMPORTS_SUCCESSFUL else 0,
        "formats": SUPPORTED_FORMATS if _IMPORTS_SUCCESSFUL else [],
        "cache_enabled": _IMPORTS_SUCCESSFUL,
        "default_cache_size": DEFAULT_CACHE_SIZE,
        "max_batch_size": MAX_BATCH_SIZE
    }

# Export all public functions and classes
__all__ = [
    # Algorithm functions
    "luhn_check",
    "luhn_calculate_check_digit",
    "verhoeff_check", 
    "verhoeff_calculate_check_digit",
    "damm_check",
    "damm_calculate_check_digit",
    "mod97_check",
    "mod97_calculate_check_digits",
    "isbn_check",
    "issn_check",
    
    # Formatting functions
    "format_credit_card",
    "format_phone_number",
    "format_ssn",
    "format_iban",
    "mask_sensitive_data",
    "progressive_disclosure",
    "international_format",
    
    # Generation functions
    "generate_test_credit_card",
    "generate_test_ssn",
    "generate_test_phone",
    "generate_test_email",
    "generate_invalid_data",
    "generate_edge_cases",
    
    # Extraction functions
    "extract_numbers",
    "extract_patterns",
    "normalize_input",
    "clean_input",
    "parse_structured_data",
    
    # Caching functions
    "LRUCache",
    "TTLCache",
    "SecureCache",
    "cache_result",
    "clear_cache",
    
    # Utility functions
    "get_available_algorithms",
    "get_supported_formats",
    "validate_algorithm_input",
    "benchmark_algorithm",
    "create_custom_formatter",
    "get_utility_info",
    
    # Types and classes
    "Algorithm",
    "AlgorithmResult",
    "FormattingStyle",
    "MaskingOptions",
    "FormatResult",
    "TestDataType",
    "GenerationOptions",
    "TestDataResult",
    "ExtractionResult",
    "ParsingOptions",
    "CacheStats",
    
    # Constants
    "ALGORITHMS",
    "SUPPORTED_FORMATS", 
    "MASKING_STYLES",
    "DEFAULT_CACHE_SIZE",
    "DEFAULT_CACHE_TTL",
    "MAX_BATCH_SIZE"
]
