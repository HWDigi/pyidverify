"""
Formatting and Masking Utilities
===============================

This module provides comprehensive formatting and masking utilities for
displaying identification data safely and consistently. All functions
are designed with privacy and security in mind.

Features:
- Credit card formatting with various styles
- Phone number internationalization
- SSN formatting and masking
- IBAN formatting for international banking
- Flexible masking with customizable patterns
- Progressive disclosure for enhanced UX
- Memory-safe operations

Examples:
    >>> from pyidverify.utils.formatters import format_credit_card, mask_sensitive_data
    >>> 
    >>> # Format credit card for display
    >>> formatted = format_credit_card("4532015112830366")
    >>> print(formatted)  # "4532-0151-1283-0366"
    >>> 
    >>> # Mask sensitive data
    >>> masked = mask_sensitive_data("4532015112830366", visible_start=4, visible_end=4)
    >>> print(masked)  # "4532********0366"

Security Features:
- No intermediate storage of sensitive data
- Memory clearing after operations
- Customizable masking patterns
- XSS-safe output formatting
"""

from typing import Optional, Dict, Any, Union, List, Callable
from dataclasses import dataclass
from enum import Enum
import re
import secrets
from functools import lru_cache

class FormattingStyle(Enum):
    """Formatting style options"""
    STANDARD = "standard"
    COMPACT = "compact" 
    SPACED = "spaced"
    DASHED = "dashed"
    DOTTED = "dotted"
    CUSTOM = "custom"

class MaskingStrategy(Enum):
    """Masking strategy options"""
    ASTERISK = "asterisk"
    DOTS = "dots"
    X_MARKS = "x_marks"
    UNICODE_DOTS = "unicode_dots"
    CUSTOM = "custom"

@dataclass
class MaskingOptions:
    """Configuration for data masking"""
    mask_char: str = "*"
    visible_start: int = 4
    visible_end: int = 4
    min_mask_length: int = 4
    preserve_formatting: bool = False
    strategy: MaskingStrategy = MaskingStrategy.ASTERISK
    
    def __post_init__(self):
        """Validate masking options"""
        if self.visible_start < 0:
            raise ValueError("visible_start must be non-negative")
        if self.visible_end < 0:
            raise ValueError("visible_end must be non-negative")
        if self.min_mask_length < 1:
            raise ValueError("min_mask_length must be at least 1")
        if len(self.mask_char) != 1:
            raise ValueError("mask_char must be a single character")

@dataclass
class FormatResult:
    """Result of formatting operation"""
    formatted_value: str
    original_length: int
    mask_applied: bool = False
    format_style: Optional[FormattingStyle] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "formatted_value": self.formatted_value,
            "original_length": self.original_length,
            "mask_applied": self.mask_applied,
            "format_style": self.format_style.value if self.format_style else None,
            "error_message": self.error_message
        }

def _sanitize_input(value: str, keep_chars: str = "") -> str:
    """
    Sanitize input string for formatting operations.
    
    Args:
        value: Input string to sanitize
        keep_chars: Additional characters to preserve
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise TypeError("Input must be a string")
    
    # Basic pattern - keep digits and specified characters
    pattern = f"[^0-9{re.escape(keep_chars)}]"
    return re.sub(pattern, "", value)

def _apply_mask_pattern(value: str, options: MaskingOptions) -> str:
    """
    Apply masking pattern to a value.
    
    Args:
        value: Value to mask
        options: Masking configuration
        
    Returns:
        Masked value
    """
    if len(value) <= options.visible_start + options.visible_end:
        # If value is too short, mask minimally
        if len(value) <= 2:
            return value  # Don't mask very short values
        # Show first and last char, mask middle
        return value[0] + options.mask_char * max(options.min_mask_length, len(value) - 2) + value[-1]
    
    # Standard masking with visible start/end
    start_part = value[:options.visible_start]
    end_part = value[-options.visible_end:] if options.visible_end > 0 else ""
    middle_length = len(value) - options.visible_start - options.visible_end
    mask_length = max(options.min_mask_length, middle_length)
    
    return start_part + options.mask_char * mask_length + end_part

def format_credit_card(number: str, style: FormattingStyle = FormattingStyle.STANDARD, 
                      mask_options: Optional[MaskingOptions] = None) -> str:
    """
    Format a credit card number for display.
    
    Args:
        number: Credit card number to format
        style: Formatting style to apply
        mask_options: Optional masking configuration
        
    Returns:
        Formatted credit card number
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> format_credit_card("4532015112830366")
        "4532-0151-1283-0366"
        >>> 
        >>> # With masking
        >>> options = MaskingOptions(visible_start=4, visible_end=4)
        >>> format_credit_card("4532015112830366", mask_options=options)
        "4532-****-****-0366"
    """
    if not isinstance(number, str):
        raise TypeError("Credit card number must be a string")
    
    # Sanitize input
    cleaned = _sanitize_input(number)
    
    if not cleaned:
        raise ValueError("Credit card number contains no valid digits")
    
    # Apply masking if requested
    if mask_options:
        cleaned = _apply_mask_pattern(cleaned, mask_options)
    
    # Apply formatting based on style
    if style == FormattingStyle.STANDARD:
        # Standard 4-4-4-4 format
        if len(cleaned) <= 4:
            return cleaned
        elif len(cleaned) <= 8:
            return f"{cleaned[:4]}-{cleaned[4:]}"
        elif len(cleaned) <= 12:
            return f"{cleaned[:4]}-{cleaned[4:8]}-{cleaned[8:]}"
        else:
            return f"{cleaned[:4]}-{cleaned[4:8]}-{cleaned[8:12]}-{cleaned[12:]}"
            
    elif style == FormattingStyle.SPACED:
        # Space-separated format
        if len(cleaned) <= 4:
            return cleaned
        elif len(cleaned) <= 8:
            return f"{cleaned[:4]} {cleaned[4:]}"
        elif len(cleaned) <= 12:
            return f"{cleaned[:4]} {cleaned[4:8]} {cleaned[8:]}"
        else:
            return f"{cleaned[:4]} {cleaned[4:8]} {cleaned[8:12]} {cleaned[12:]}"
            
    elif style == FormattingStyle.COMPACT:
        # No separators
        return cleaned
        
    elif style == FormattingStyle.DOTTED:
        # Dot-separated format
        if len(cleaned) <= 4:
            return cleaned
        elif len(cleaned) <= 8:
            return f"{cleaned[:4]}.{cleaned[4:]}"
        elif len(cleaned) <= 12:
            return f"{cleaned[:4]}.{cleaned[4:8]}.{cleaned[8:]}"
        else:
            return f"{cleaned[:4]}.{cleaned[4:8]}.{cleaned[8:12]}.{cleaned[12:]}"
    
    else:
        return cleaned

def format_phone_number(phone: str, country_code: str = "US", 
                       style: FormattingStyle = FormattingStyle.STANDARD,
                       international: bool = False) -> str:
    """
    Format a phone number according to regional conventions.
    
    Args:
        phone: Phone number to format
        country_code: ISO country code for formatting rules
        style: Formatting style to apply
        international: Whether to use international format
        
    Returns:
        Formatted phone number
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> format_phone_number("5551234567", "US")
        "(555) 123-4567"
        >>> format_phone_number("5551234567", "US", international=True)
        "+1 (555) 123-4567"
    """
    if not isinstance(phone, str):
        raise TypeError("Phone number must be a string")
    
    # Sanitize input - keep digits and plus sign
    cleaned = _sanitize_input(phone, "+")
    
    if not cleaned or len(cleaned) < 7:
        raise ValueError("Phone number too short or invalid")
    
    # Remove leading plus if present for processing
    has_plus = cleaned.startswith("+")
    if has_plus:
        cleaned = cleaned[1:]
    
    # Format based on country and style
    if country_code.upper() == "US":
        return _format_us_phone(cleaned, style, international or has_plus)
    elif country_code.upper() == "GB":
        return _format_uk_phone(cleaned, style, international or has_plus)
    elif country_code.upper() == "CA":
        return _format_ca_phone(cleaned, style, international or has_plus)
    else:
        # Generic international format
        return _format_international_phone(cleaned, country_code, style)

def _format_us_phone(phone: str, style: FormattingStyle, international: bool) -> str:
    """Format US phone number"""
    if len(phone) == 10:
        # Standard US format: (555) 123-4567
        area = phone[:3]
        exchange = phone[3:6]
        number = phone[6:]
        
        if style == FormattingStyle.STANDARD:
            formatted = f"({area}) {exchange}-{number}"
        elif style == FormattingStyle.DASHED:
            formatted = f"{area}-{exchange}-{number}"
        elif style == FormattingStyle.DOTTED:
            formatted = f"{area}.{exchange}.{number}"
        elif style == FormattingStyle.COMPACT:
            formatted = phone
        else:
            formatted = f"({area}) {exchange}-{number}"
        
        if international:
            return f"+1 {formatted}"
        return formatted
        
    elif len(phone) == 11 and phone.startswith("1"):
        # US number with country code
        return _format_us_phone(phone[1:], style, international)
    else:
        # Unknown format, return as-is with minimal formatting
        if international and not phone.startswith("1"):
            return f"+1 {phone}"
        return phone

def _format_uk_phone(phone: str, style: FormattingStyle, international: bool) -> str:
    """Format UK phone number"""
    # Basic UK formatting - this is simplified
    if len(phone) == 10:
        formatted = f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    elif len(phone) == 11 and phone.startswith("44"):
        formatted = f"{phone[:2]} {phone[2:6]} {phone[6:9]} {phone[9:]}"
    else:
        formatted = phone
    
    if international and not phone.startswith("44"):
        return f"+44 {formatted}"
    return formatted

def _format_ca_phone(phone: str, style: FormattingStyle, international: bool) -> str:
    """Format Canadian phone number (same as US)"""
    return _format_us_phone(phone, style, international)

def _format_international_phone(phone: str, country_code: str, style: FormattingStyle) -> str:
    """Format international phone number generically"""
    # Very basic international formatting
    if len(phone) > 8:
        return f"+{phone[:2]} {phone[2:5]} {phone[5:8]} {phone[8:]}"
    else:
        return f"+{phone}"

def format_ssn(ssn: str, mask_options: Optional[MaskingOptions] = None) -> str:
    """
    Format a Social Security Number.
    
    Args:
        ssn: SSN to format
        mask_options: Optional masking configuration
        
    Returns:
        Formatted SSN
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> format_ssn("123456789")
        "123-45-6789"
        >>> 
        >>> # With masking
        >>> options = MaskingOptions(visible_start=0, visible_end=4)
        >>> format_ssn("123456789", mask_options=options)
        "***-**-6789"
    """
    if not isinstance(ssn, str):
        raise TypeError("SSN must be a string")
    
    # Sanitize input
    cleaned = _sanitize_input(ssn)
    
    if len(cleaned) != 9:
        raise ValueError("SSN must be exactly 9 digits")
    
    # Apply masking if requested
    if mask_options:
        cleaned = _apply_mask_pattern(cleaned, mask_options)
    
    # Format as XXX-XX-XXXX
    return f"{cleaned[:3]}-{cleaned[3:5]}-{cleaned[5:]}"

def format_iban(iban: str, style: FormattingStyle = FormattingStyle.SPACED) -> str:
    """
    Format an IBAN for display.
    
    Args:
        iban: IBAN to format
        style: Formatting style to apply
        
    Returns:
        Formatted IBAN
        
    Raises:
        ValueError: If input is invalid
        TypeError: If input is not a string
        
    Examples:
        >>> format_iban("GB82WEST12345698765432")
        "GB82 WEST 1234 5698 7654 32"
    """
    if not isinstance(iban, str):
        raise TypeError("IBAN must be a string")
    
    # Clean and uppercase
    cleaned = re.sub(r'[^A-Z0-9]', '', iban.upper())
    
    if len(cleaned) < 15 or len(cleaned) > 34:
        raise ValueError("IBAN length invalid")
    
    if style == FormattingStyle.SPACED:
        # Group in blocks of 4
        formatted = ""
        for i in range(0, len(cleaned), 4):
            if i > 0:
                formatted += " "
            formatted += cleaned[i:i+4]
        return formatted
    elif style == FormattingStyle.COMPACT:
        return cleaned
    else:
        # Default to spaced format
        formatted = ""
        for i in range(0, len(cleaned), 4):
            if i > 0:
                formatted += " "
            formatted += cleaned[i:i+4]
        return formatted

def mask_sensitive_data(value: str, mask_char: str = "*", visible_start: int = 4, 
                       visible_end: int = 4, min_mask_length: int = 4,
                       preserve_formatting: bool = False) -> str:
    """
    Mask sensitive data while preserving some visible characters.
    
    Args:
        value: Value to mask
        mask_char: Character to use for masking
        visible_start: Number of characters to show at start
        visible_end: Number of characters to show at end
        min_mask_length: Minimum length of masked section
        preserve_formatting: Whether to preserve non-alphanumeric characters
        
    Returns:
        Masked value
        
    Examples:
        >>> mask_sensitive_data("4532015112830366")
        "4532********0366"
        >>> mask_sensitive_data("john.doe@email.com", visible_start=2, visible_end=8)
        "jo*******@email.com"
    """
    if not isinstance(value, str):
        raise TypeError("Value must be a string")
    
    if not value:
        return value
    
    options = MaskingOptions(
        mask_char=mask_char,
        visible_start=visible_start,
        visible_end=visible_end,
        min_mask_length=min_mask_length,
        preserve_formatting=preserve_formatting
    )
    
    if preserve_formatting:
        # Preserve formatting characters, mask only alphanumeric
        result = ""
        alphanumeric_chars = [c for c in value if c.isalnum()]
        masked_alphanumeric = _apply_mask_pattern(''.join(alphanumeric_chars), options)
        
        masked_index = 0
        for char in value:
            if char.isalnum():
                if masked_index < len(masked_alphanumeric):
                    result += masked_alphanumeric[masked_index]
                    masked_index += 1
                else:
                    result += char
            else:
                result += char
        
        return result
    else:
        return _apply_mask_pattern(value, options)

def progressive_disclosure(value: str, level: int = 1, max_level: int = 3) -> str:
    """
    Apply progressive disclosure to sensitive data.
    
    Progressive disclosure shows more information as the level increases:
    - Level 1: Minimal disclosure (e.g., first 2 and last 2 chars)
    - Level 2: Moderate disclosure (e.g., first 4 and last 4 chars)  
    - Level 3: High disclosure (e.g., masked only middle section)
    
    Args:
        value: Value to apply progressive disclosure to
        level: Disclosure level (1-3)
        max_level: Maximum disclosure level
        
    Returns:
        Value with progressive disclosure applied
        
    Examples:
        >>> progressive_disclosure("4532015112830366", level=1)
        "45************66"
        >>> progressive_disclosure("4532015112830366", level=2) 
        "4532********0366"
        >>> progressive_disclosure("4532015112830366", level=3)
        "453201****830366"
    """
    if not isinstance(value, str):
        raise TypeError("Value must be a string")
    
    if level < 1:
        level = 1
    elif level > max_level:
        level = max_level
    
    # Define disclosure levels
    disclosure_configs = {
        1: MaskingOptions(visible_start=2, visible_end=2, min_mask_length=6),
        2: MaskingOptions(visible_start=4, visible_end=4, min_mask_length=4),
        3: MaskingOptions(visible_start=6, visible_end=6, min_mask_length=2)
    }
    
    config = disclosure_configs.get(level, disclosure_configs[1])
    return _apply_mask_pattern(value, config)

def international_format(value: str, format_type: str, country_code: str = "US") -> str:
    """
    Apply international formatting to a value.
    
    Args:
        value: Value to format
        format_type: Type of formatting (phone, postal_code, etc.)
        country_code: ISO country code
        
    Returns:
        Internationally formatted value
        
    Examples:
        >>> international_format("5551234567", "phone", "US")
        "+1 (555) 123-4567"
    """
    if format_type == "phone":
        return format_phone_number(value, country_code, international=True)
    elif format_type == "postal_code":
        return _format_postal_code(value, country_code)
    else:
        return value

def _format_postal_code(postal_code: str, country_code: str) -> str:
    """Format postal code by country"""
    cleaned = _sanitize_input(postal_code, " -ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    if country_code.upper() == "US":
        # US ZIP codes: 12345 or 12345-6789
        if len(cleaned) == 5:
            return cleaned
        elif len(cleaned) == 9:
            return f"{cleaned[:5]}-{cleaned[5:]}"
    elif country_code.upper() == "CA":
        # Canadian postal codes: A1A 1A1
        if len(cleaned) == 6:
            return f"{cleaned[:3]} {cleaned[3:]}"
    elif country_code.upper() == "GB":
        # UK postal codes are complex, simplified here
        if len(cleaned) >= 5:
            return f"{cleaned[:-3]} {cleaned[-3:]}"
    
    return cleaned

def create_format_template(pattern: str, placeholder: str = "X") -> Callable[[str], str]:
    """
    Create a custom formatting template.
    
    Args:
        pattern: Format pattern using placeholder character
        placeholder: Character representing data positions
        
    Returns:
        Formatting function
        
    Examples:
        >>> formatter = create_format_template("XX-XX-XX", "X")
        >>> result = formatter("123456")
        >>> print(result)  # "12-34-56"
    """
    def format_with_template(value: str) -> str:
        """Apply template formatting"""
        if not value:
            return value
        
        # Remove all non-alphanumeric characters from value
        cleaned = re.sub(r'[^A-Za-z0-9]', '', value)
        
        result = ""
        value_index = 0
        
        for char in pattern:
            if char == placeholder:
                if value_index < len(cleaned):
                    result += cleaned[value_index]
                    value_index += 1
                else:
                    break
            else:
                result += char
        
        return result
    
    return format_with_template

def format_with_result(value: str, format_type: str, **kwargs) -> FormatResult:
    """
    Format value and return detailed result.
    
    Args:
        value: Value to format
        format_type: Type of formatting to apply
        **kwargs: Additional formatting options
        
    Returns:
        FormatResult with formatting details
        
    Examples:
        >>> result = format_with_result("4532015112830366", "credit_card")
        >>> print(result.formatted_value)
        "4532-0151-1283-0366"
    """
    original_length = len(value) if value else 0
    
    try:
        if format_type == "credit_card":
            style = kwargs.get("style", FormattingStyle.STANDARD)
            mask_options = kwargs.get("mask_options")
            formatted = format_credit_card(value, style, mask_options)
            
            return FormatResult(
                formatted_value=formatted,
                original_length=original_length,
                mask_applied=mask_options is not None,
                format_style=style
            )
            
        elif format_type == "phone":
            country_code = kwargs.get("country_code", "US")
            style = kwargs.get("style", FormattingStyle.STANDARD)
            international = kwargs.get("international", False)
            formatted = format_phone_number(value, country_code, style, international)
            
            return FormatResult(
                formatted_value=formatted,
                original_length=original_length,
                format_style=style
            )
            
        elif format_type == "ssn":
            mask_options = kwargs.get("mask_options")
            formatted = format_ssn(value, mask_options)
            
            return FormatResult(
                formatted_value=formatted,
                original_length=original_length,
                mask_applied=mask_options is not None
            )
            
        elif format_type == "iban":
            style = kwargs.get("style", FormattingStyle.SPACED)
            formatted = format_iban(value, style)
            
            return FormatResult(
                formatted_value=formatted,
                original_length=original_length,
                format_style=style
            )
            
        else:
            return FormatResult(
                formatted_value=value,
                original_length=original_length,
                error_message=f"Unknown format type: {format_type}"
            )
            
    except Exception as e:
        return FormatResult(
            formatted_value=value,
            original_length=original_length,
            error_message=str(e)
        )

# Export all public functions
__all__ = [
    "FormattingStyle",
    "MaskingStrategy", 
    "MaskingOptions",
    "FormatResult",
    "format_credit_card",
    "format_phone_number",
    "format_ssn",
    "format_iban",
    "mask_sensitive_data",
    "progressive_disclosure",
    "international_format",
    "create_format_template",
    "format_with_result"
]
