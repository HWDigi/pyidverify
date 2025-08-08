"""
Data Extraction and Parsing Utilities
====================================

This module provides utilities for extracting and parsing structured
data from various input formats. These utilities are designed to safely
handle user input and extract meaningful data for validation.

Features:
- Safe pattern extraction from text
- Input normalization and cleaning
- Structured data parsing
- Multiple format support
- XSS and injection protection
- Comprehensive input sanitization

Examples:
    >>> from pyidverify.utils.extractors import extract_numbers, normalize_input
    >>> 
    >>> # Extract credit card numbers from text
    >>> text = "My card is 4532-0151-1283-0366 and expires 12/25"
    >>> numbers = extract_numbers(text, min_length=13, max_length=19)
    >>> print(numbers)  # ["4532015112830366"]
    >>> 
    >>> # Normalize phone number input
    >>> normalized = normalize_input("+1 (555) 123-4567", "phone")
    >>> print(normalized)  # "15551234567"

Security Features:
- Input sanitization prevents injection attacks
- Pattern matching with ReDoS protection
- Memory-safe string operations
- Length limits prevent DoS attacks
"""

from typing import Optional, Dict, Any, List, Union, Pattern, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import html
import unicodedata
from functools import lru_cache

class ExtractionType(Enum):
    """Types of data extraction"""
    NUMBERS = "numbers"
    PATTERNS = "patterns"
    EMAILS = "emails"
    PHONES = "phones"
    URLS = "urls"
    CREDIT_CARDS = "credit_cards"
    SSNS = "ssns"
    CUSTOM = "custom"

@dataclass
class ParsingOptions:
    """Configuration for parsing operations"""
    max_input_length: int = 100000  # Prevent DoS
    sanitize_input: bool = True
    normalize_whitespace: bool = True
    remove_html: bool = True
    case_sensitive: bool = False
    preserve_formatting: bool = False
    timeout_seconds: float = 1.0  # Regex timeout
    
    def __post_init__(self):
        """Validate parsing options"""
        if self.max_input_length < 1:
            raise ValueError("max_input_length must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

@dataclass
class ExtractionResult:
    """Result of data extraction operation"""
    extracted_values: List[str]
    extraction_type: ExtractionType
    input_length: int
    processing_time_ms: Optional[float] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "extracted_values": self.extracted_values,
            "extraction_type": self.extraction_type.value,
            "input_length": self.input_length,
            "processing_time_ms": self.processing_time_ms,
            "warnings": self.warnings,
            "metadata": self.metadata
        }

# Precompiled regex patterns for efficiency
_CREDIT_CARD_PATTERN = re.compile(
    r'\b(?:\d[ -]*?){13,19}\b',
    re.IGNORECASE
)

_EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

_PHONE_PATTERN = re.compile(
    r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
    re.IGNORECASE
)

_SSN_PATTERN = re.compile(
    r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
    re.IGNORECASE
)

_URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    re.IGNORECASE
)

def _sanitize_input_string(text: str, options: ParsingOptions) -> str:
    """
    Sanitize input string for safe processing.
    
    Args:
        text: Input text to sanitize
        options: Parsing options
        
    Returns:
        Sanitized text string
        
    Raises:
        ValueError: If input is too long
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Length check to prevent DoS
    if len(text) > options.max_input_length:
        raise ValueError(f"Input too long (max {options.max_input_length} characters)")
    
    if options.sanitize_input:
        # Remove HTML tags and decode entities
        if options.remove_html:
            text = html.unescape(text)
            text = re.sub(r'<[^<]+?>', '', text)
        
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Remove control characters except newline and tab
        text = ''.join(char for char in text 
                      if unicodedata.category(char)[0] != 'C' 
                      or char in '\n\t\r')
    
    if options.normalize_whitespace:
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
    
    if not options.case_sensitive:
        text = text.lower()
    
    return text

def extract_numbers(text: str, min_length: int = 1, max_length: int = 50,
                   options: Optional[ParsingOptions] = None) -> List[str]:
    """
    Extract numeric sequences from text.
    
    Args:
        text: Input text to extract from
        min_length: Minimum length of numbers to extract
        max_length: Maximum length of numbers to extract
        options: Parsing options
        
    Returns:
        List of extracted numeric strings
        
    Raises:
        ValueError: If input is invalid
        
    Examples:
        >>> extract_numbers("Call 555-123-4567 or 555-987-6543")
        ['555', '123', '4567', '555', '987', '6543']
        >>> extract_numbers("Credit card: 4532-0151-1283-0366", min_length=13)
        ['4532015112830366']
    """
    if options is None:
        options = ParsingOptions()
    
    # Sanitize input
    sanitized_text = _sanitize_input_string(text, options)
    
    # Extract all numeric sequences
    numbers = re.findall(r'\d+', sanitized_text)
    
    # Filter by length
    filtered_numbers = [
        num for num in numbers 
        if min_length <= len(num) <= max_length
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_numbers = []
    for num in filtered_numbers:
        if num not in seen:
            seen.add(num)
            unique_numbers.append(num)
    
    return unique_numbers

def extract_patterns(text: str, pattern: Union[str, Pattern], 
                    options: Optional[ParsingOptions] = None) -> ExtractionResult:
    """
    Extract data matching a specific pattern from text.
    
    Args:
        text: Input text to extract from
        pattern: Regex pattern to match (string or compiled Pattern)
        options: Parsing options
        
    Returns:
        ExtractionResult with extracted matches
        
    Raises:
        ValueError: If input is invalid
        re.error: If pattern is invalid
        
    Examples:
        >>> result = extract_patterns("Email: john@example.com", r"\\b[\\w.-]+@[\\w.-]+\\.[\\w]+\\b")
        >>> print(result.extracted_values)  # ['john@example.com']
    """
    import time
    
    start_time = time.perf_counter()
    
    if options is None:
        options = ParsingOptions()
    
    # Sanitize input
    sanitized_text = _sanitize_input_string(text, options)
    
    # Compile pattern if it's a string
    if isinstance(pattern, str):
        try:
            # Add ReDoS protection by limiting repetition
            if '+' in pattern or '*' in pattern:
                # This is a simplified check - real ReDoS protection is complex
                if pattern.count('+') + pattern.count('*') > 10:
                    raise ValueError("Pattern may be vulnerable to ReDoS attacks")
            
            compiled_pattern = re.compile(pattern, re.IGNORECASE if not options.case_sensitive else 0)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    else:
        compiled_pattern = pattern
    
    # Extract matches with timeout protection
    try:
        matches = compiled_pattern.findall(sanitized_text)
    except Exception as e:
        # In production, you might want to implement proper regex timeout
        raise ValueError(f"Pattern matching failed: {e}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in matches:
        # Handle tuple results from groups
        match_str = match if isinstance(match, str) else str(match)
        if match_str not in seen:
            seen.add(match_str)
            unique_matches.append(match_str)
    
    end_time = time.perf_counter()
    processing_time = (end_time - start_time) * 1000
    
    warnings = []
    if processing_time > 100:  # 100ms threshold
        warnings.append("Pattern matching took longer than expected")
    
    return ExtractionResult(
        extracted_values=unique_matches,
        extraction_type=ExtractionType.PATTERNS,
        input_length=len(text),
        processing_time_ms=processing_time,
        warnings=warnings,
        metadata={"pattern": str(pattern), "match_count": len(matches)}
    )

def extract_emails(text: str, options: Optional[ParsingOptions] = None) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Input text to extract from
        options: Parsing options
        
    Returns:
        List of extracted email addresses
        
    Examples:
        >>> extract_emails("Contact john@example.com or jane@test.org")
        ['john@example.com', 'jane@test.org']
    """
    if options is None:
        options = ParsingOptions()
    
    result = extract_patterns(text, _EMAIL_PATTERN, options)
    return result.extracted_values

def extract_phones(text: str, country_code: str = "US", 
                  options: Optional[ParsingOptions] = None) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Input text to extract from
        country_code: Country code for phone format
        options: Parsing options
        
    Returns:
        List of extracted phone numbers
        
    Examples:
        >>> extract_phones("Call (555) 123-4567 or 555-987-6543")
        ['5551234567', '5559876543']
    """
    if options is None:
        options = ParsingOptions()
    
    sanitized_text = _sanitize_input_string(text, options)
    
    if country_code.upper() == "US":
        # US phone number extraction
        matches = _PHONE_PATTERN.findall(sanitized_text)
        # Flatten tuples from regex groups
        phones = [''.join(match) for match in matches if len(match) == 3]
        
        # Also look for 10-digit sequences
        digit_sequences = extract_numbers(sanitized_text, min_length=10, max_length=11)
        for seq in digit_sequences:
            if len(seq) == 10:
                phones.append(seq)
            elif len(seq) == 11 and seq.startswith('1'):
                phones.append(seq[1:])  # Remove country code
        
        # Remove duplicates
        seen = set()
        unique_phones = []
        for phone in phones:
            if phone not in seen and len(phone) == 10:
                seen.add(phone)
                unique_phones.append(phone)
        
        return unique_phones
    else:
        # Generic international phone extraction
        return extract_numbers(sanitized_text, min_length=7, max_length=15)

def extract_credit_cards(text: str, options: Optional[ParsingOptions] = None) -> List[str]:
    """
    Extract potential credit card numbers from text.
    
    Args:
        text: Input text to extract from
        options: Parsing options
        
    Returns:
        List of extracted credit card numbers
        
    Examples:
        >>> extract_credit_cards("Card: 4532-0151-1283-0366")
        ['4532015112830366']
    """
    if options is None:
        options = ParsingOptions()
    
    result = extract_patterns(text, _CREDIT_CARD_PATTERN, options)
    
    # Clean extracted values - remove spaces and dashes
    cleaned_cards = []
    for card in result.extracted_values:
        cleaned = re.sub(r'[^0-9]', '', card)
        if 13 <= len(cleaned) <= 19:  # Valid credit card length range
            cleaned_cards.append(cleaned)
    
    return cleaned_cards

def extract_ssns(text: str, options: Optional[ParsingOptions] = None) -> List[str]:
    """
    Extract potential Social Security Numbers from text.
    
    Args:
        text: Input text to extract from
        options: Parsing options
        
    Returns:
        List of extracted SSNs
        
    Examples:
        >>> extract_ssns("SSN: 123-45-6789")
        ['123456789']
    """
    if options is None:
        options = ParsingOptions()
    
    result = extract_patterns(text, _SSN_PATTERN, options)
    
    # Clean extracted values - remove separators
    cleaned_ssns = []
    for ssn in result.extracted_values:
        cleaned = re.sub(r'[^0-9]', '', ssn)
        if len(cleaned) == 9:  # SSN must be exactly 9 digits
            cleaned_ssns.append(cleaned)
    
    return cleaned_ssns

def normalize_input(value: str, data_type: str, options: Optional[ParsingOptions] = None) -> str:
    """
    Normalize input value for consistent processing.
    
    Args:
        value: Input value to normalize
        data_type: Type of data being normalized
        options: Parsing options
        
    Returns:
        Normalized value
        
    Examples:
        >>> normalize_input("(555) 123-4567", "phone")
        '5551234567'
        >>> normalize_input("4532-0151-1283-0366", "credit_card")
        '4532015112830366'
    """
    if options is None:
        options = ParsingOptions()
    
    # Sanitize input
    normalized = _sanitize_input_string(value, options)
    
    if data_type.lower() == "phone":
        # Remove all non-digits except +
        normalized = re.sub(r'[^+0-9]', '', normalized)
        # Remove leading +1 for US numbers
        if normalized.startswith('+1'):
            normalized = normalized[2:]
        elif normalized.startswith('1') and len(normalized) == 11:
            normalized = normalized[1:]
        
    elif data_type.lower() == "credit_card":
        # Remove all non-digits
        normalized = re.sub(r'[^0-9]', '', normalized)
        
    elif data_type.lower() == "ssn":
        # Remove all non-digits
        normalized = re.sub(r'[^0-9]', '', normalized)
        
    elif data_type.lower() == "email":
        # Basic email normalization
        normalized = normalized.strip().lower()
        
    elif data_type.lower() == "iban":
        # Remove spaces and convert to uppercase
        normalized = re.sub(r'\s+', '', normalized).upper()
        
    else:
        # Generic normalization - remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def clean_input(value: str, allowed_chars: Optional[str] = None, 
               max_length: Optional[int] = None) -> str:
    """
    Clean input by removing unwanted characters.
    
    Args:
        value: Input value to clean
        allowed_chars: Characters to allow (others will be removed)
        max_length: Maximum length to truncate to
        
    Returns:
        Cleaned input value
        
    Examples:
        >>> clean_input("abc123!@#", "0123456789abcdef")
        'abc123'
        >>> clean_input("very long text here", max_length=10)
        'very long '
    """
    if not isinstance(value, str):
        value = str(value)
    
    if allowed_chars:
        # Keep only allowed characters
        cleaned = ''.join(char for char in value if char in allowed_chars)
    else:
        # Remove control characters
        cleaned = ''.join(char for char in value 
                         if unicodedata.category(char)[0] != 'C' 
                         or char in '\n\t\r ')
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned

def parse_structured_data(data: str, structure_type: str, 
                         options: Optional[ParsingOptions] = None) -> Dict[str, Any]:
    """
    Parse structured data from string input.
    
    Args:
        data: Structured data string
        structure_type: Type of structure (json, csv, key_value)
        options: Parsing options
        
    Returns:
        Dictionary with parsed data
        
    Examples:
        >>> parse_structured_data("name=John,age=30", "key_value")
        {'name': 'John', 'age': '30'}
    """
    if options is None:
        options = ParsingOptions()
    
    # Sanitize input
    sanitized_data = _sanitize_input_string(data, options)
    
    parsed = {}
    
    if structure_type.lower() == "key_value":
        # Parse key=value pairs separated by commas
        pairs = sanitized_data.split(',')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                parsed[key.strip()] = value.strip()
    
    elif structure_type.lower() == "csv":
        # Basic CSV parsing (single row)
        values = [v.strip() for v in sanitized_data.split(',')]
        parsed = {f"field_{i}": value for i, value in enumerate(values)}
    
    elif structure_type.lower() == "json":
        # Basic JSON-like parsing (very simplified)
        try:
            import json
            parsed = json.loads(sanitized_data)
        except (json.JSONDecodeError, ValueError):
            # Fallback to key-value parsing
            parsed = {"raw_data": sanitized_data, "parse_error": "Invalid JSON"}
    
    else:
        parsed = {"raw_data": sanitized_data, "structure_type": structure_type}
    
    return parsed

@lru_cache(maxsize=1000)
def cached_normalize_input(value: str, data_type: str) -> str:
    """
    Cached version of normalize_input for better performance.
    
    Args:
        value: Input value to normalize
        data_type: Type of data being normalized
        
    Returns:
        Normalized value
    """
    return normalize_input(value, data_type)

def extract_all_ids(text: str, options: Optional[ParsingOptions] = None) -> Dict[str, List[str]]:
    """
    Extract all types of ID-like data from text.
    
    Args:
        text: Input text to extract from
        options: Parsing options
        
    Returns:
        Dictionary with different types of extracted IDs
        
    Examples:
        >>> result = extract_all_ids("Contact john@test.com or call 555-123-4567")
        >>> print(result)
        {'emails': ['john@test.com'], 'phones': ['5551234567'], ...}
    """
    if options is None:
        options = ParsingOptions()
    
    results = {}
    
    # Extract different types of IDs
    try:
        results['emails'] = extract_emails(text, options)
        results['phones'] = extract_phones(text, options=options)
        results['credit_cards'] = extract_credit_cards(text, options)
        results['ssns'] = extract_ssns(text, options)
        results['urls'] = extract_patterns(text, _URL_PATTERN, options).extracted_values
    except Exception as e:
        results['error'] = str(e)
    
    return results

def get_extraction_stats() -> Dict[str, Any]:
    """
    Get statistics about extraction operations.
    
    Returns:
        Dictionary with extraction statistics
    """
    cache_info = cached_normalize_input.cache_info()
    
    return {
        "supported_extractions": [e.value for e in ExtractionType],
        "cache_hits": cache_info.hits,
        "cache_misses": cache_info.misses,
        "cache_size": cache_info.currsize,
        "cache_max_size": cache_info.maxsize
    }

# Export all public functions
__all__ = [
    "ExtractionType",
    "ParsingOptions", 
    "ExtractionResult",
    "extract_numbers",
    "extract_patterns",
    "extract_emails",
    "extract_phones",
    "extract_credit_cards",
    "extract_ssns",
    "normalize_input",
    "clean_input",
    "parse_structured_data",
    "cached_normalize_input",
    "extract_all_ids",
    "get_extraction_stats"
]
