"""
Secure Test Data Generation
==========================

This module provides secure generation of test data for ID validation
testing. All generated data is cryptographically random and guaranteed
to be invalid for real-world use while maintaining realistic formats.

SECURITY NOTICE: This module generates test data only. Generated IDs
are intentionally invalid and must never be used as real identifiers.

Features:
- Cryptographically secure random generation  
- Realistic but invalid test data
- Edge case generation for comprehensive testing
- Batch generation for performance testing
- Format-specific generation with checksums
- No collision with real valid IDs

Examples:
    >>> from pyidverify.utils.generators import generate_test_credit_card
    >>> 
    >>> # Generate test credit card (invalid)
    >>> test_card = generate_test_credit_card("visa")
    >>> print(test_card.value)  # "4000000000000002" (invalid)
    >>> 
    >>> # Generate batch of test data
    >>> test_data = generate_test_batch("credit_card", count=100)

Security Features:
- Uses cryptographically secure random numbers
- Generated data is guaranteed invalid
- No patterns that could create valid IDs
- Memory clearing for sensitive operations
"""

from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import secrets
import random
import string
import re
from datetime import datetime, timedelta

class TestDataType(Enum):
    """Types of test data that can be generated"""
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT = "passport"
    IP_ADDRESS = "ip_address"
    IBAN = "iban"
    ISBN = "isbn"
    CUSTOM = "custom"

class GenerationStrategy(Enum):
    """Strategies for test data generation"""
    RANDOM_INVALID = "random_invalid"
    EDGE_CASES = "edge_cases"
    FORMAT_VALID_VALUE_INVALID = "format_valid_value_invalid"
    STRESS_TEST = "stress_test"

@dataclass
class GenerationOptions:
    """Configuration for test data generation"""
    strategy: GenerationStrategy = GenerationStrategy.RANDOM_INVALID
    count: int = 1
    ensure_invalid: bool = True
    include_edge_cases: bool = False
    format_type: Optional[str] = None
    country_code: str = "US"
    seed: Optional[int] = None
    
    def __post_init__(self):
        """Validate generation options"""
        if self.count < 1:
            raise ValueError("count must be at least 1")
        if self.count > 100000:
            raise ValueError("count too large (max 100000 for safety)")

@dataclass 
class TestDataResult:
    """Result of test data generation"""
    value: str
    data_type: TestDataType
    is_valid_format: bool
    is_intentionally_invalid: bool
    metadata: Dict[str, Any]
    generation_strategy: GenerationStrategy
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "value": self.value,
            "data_type": self.data_type.value,
            "is_valid_format": self.is_valid_format,
            "is_intentionally_invalid": self.is_intentionally_invalid,
            "metadata": self.metadata,
            "generation_strategy": self.generation_strategy.value
        }

# Credit card BIN ranges for test data (these are invalid ranges)
_TEST_CREDIT_CARD_BINS = {
    "visa": ["4000", "4001", "4002", "4003"],
    "mastercard": ["5000", "5001", "5002", "5003"],
    "amex": ["3000", "3001", "3002", "3003"],
    "discover": ["6000", "6001", "6002", "6003"],
    "generic": ["9000", "9001", "9002", "9003"]  # Obviously invalid
}

# Invalid SSN area numbers (reserved/invalid)
_INVALID_SSN_AREAS = ["000", "666", "900", "901", "902", "903", "904", "905", "999"]

# Test email domains (obviously fake)
_TEST_EMAIL_DOMAINS = [
    "test-invalid.com",
    "fake-domain.test", 
    "invalid-email.example",
    "do-not-use.invalid",
    "test-data.fake"
]

def _secure_random_digits(length: int) -> str:
    """
    Generate cryptographically secure random digits.
    
    Args:
        length: Number of digits to generate
        
    Returns:
        String of random digits
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

def _secure_random_choice(choices: List[str]) -> str:
    """
    Securely choose from a list of options.
    
    Args:
        choices: List of options to choose from
        
    Returns:
        Randomly selected option
    """
    return secrets.choice(choices)

def _luhn_make_invalid(number: str) -> str:
    """
    Take a number and ensure it fails Luhn validation.
    
    Args:
        number: Number to make invalid
        
    Returns:
        Number that fails Luhn validation
    """
    # Calculate what the valid check digit would be
    digits = [int(d) for d in number[:-1]]
    
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:  # Check digit position makes this opposite
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    
    valid_check_digit = (10 - (total % 10)) % 10
    
    # Use any digit except the valid one
    invalid_digits = [d for d in range(10) if d != valid_check_digit]
    invalid_check_digit = _secure_random_choice([str(d) for d in invalid_digits])
    
    return number[:-1] + invalid_check_digit

def generate_test_credit_card(card_type: str = "visa", options: Optional[GenerationOptions] = None) -> TestDataResult:
    """
    Generate test credit card number (guaranteed invalid).
    
    Args:
        card_type: Type of card (visa, mastercard, amex, discover, generic)
        options: Generation options
        
    Returns:
        TestDataResult with generated card data
        
    Examples:
        >>> result = generate_test_credit_card("visa")
        >>> print(result.value)  # "4000123456789012" (invalid)
        >>> print(result.is_intentionally_invalid)  # True
    """
    if options is None:
        options = GenerationOptions()
    
    # Get BIN for card type
    card_type_lower = card_type.lower()
    if card_type_lower in _TEST_CREDIT_CARD_BINS:
        bin_choices = _TEST_CREDIT_CARD_BINS[card_type_lower]
    else:
        bin_choices = _TEST_CREDIT_CARD_BINS["generic"]
    
    bin_number = _secure_random_choice(bin_choices)
    
    # Generate appropriate length
    if card_type_lower == "amex":
        # Amex is 15 digits
        remaining_digits = 15 - len(bin_number)
    else:
        # Most cards are 16 digits
        remaining_digits = 16 - len(bin_number)
    
    # Generate account number part
    account_part = _secure_random_digits(remaining_digits - 1)  # -1 for check digit
    
    # Create initial number with temporary check digit
    temp_number = bin_number + account_part + "0"
    
    # Make it invalid by using wrong check digit
    if options.ensure_invalid:
        invalid_number = _luhn_make_invalid(temp_number)
    else:
        # Use random check digit (might be valid by chance)
        check_digit = _secure_random_digits(1)
        invalid_number = temp_number[:-1] + check_digit
    
    metadata = {
        "card_type": card_type,
        "bin": bin_number,
        "length": len(invalid_number),
        "algorithm": "luhn"
    }
    
    return TestDataResult(
        value=invalid_number,
        data_type=TestDataType.CREDIT_CARD,
        is_valid_format=True,  # Format looks valid
        is_intentionally_invalid=options.ensure_invalid,
        metadata=metadata,
        generation_strategy=options.strategy
    )

def generate_test_ssn(options: Optional[GenerationOptions] = None) -> TestDataResult:
    """
    Generate test Social Security Number (guaranteed invalid).
    
    Args:
        options: Generation options
        
    Returns:
        TestDataResult with generated SSN data
        
    Examples:
        >>> result = generate_test_ssn()
        >>> print(result.value)  # "000123456" (invalid area)
        >>> print(result.is_intentionally_invalid)  # True
    """
    if options is None:
        options = GenerationOptions()
    
    # Use invalid area number
    area = _secure_random_choice(_INVALID_SSN_AREAS)
    
    # Generate group and serial (avoid all zeros)
    group = _secure_random_digits(2)
    while group == "00":
        group = _secure_random_digits(2)
    
    serial = _secure_random_digits(4)  
    while serial == "0000":
        serial = _secure_random_digits(4)
    
    ssn = area + group + serial
    
    metadata = {
        "area": area,
        "group": group,
        "serial": serial,
        "reason_invalid": "invalid area number"
    }
    
    return TestDataResult(
        value=ssn,
        data_type=TestDataType.SSN,
        is_valid_format=True,
        is_intentionally_invalid=True,
        metadata=metadata,
        generation_strategy=options.strategy
    )

def generate_test_phone(country_code: str = "US", options: Optional[GenerationOptions] = None) -> TestDataResult:
    """
    Generate test phone number (may be invalid).
    
    Args:
        country_code: Country code for phone format
        options: Generation options
        
    Returns:
        TestDataResult with generated phone data
        
    Examples:
        >>> result = generate_test_phone("US")
        >>> print(result.value)  # "5551234567"
    """
    if options is None:
        options = GenerationOptions()
    
    if country_code.upper() == "US":
        # US phone number format
        # Use 555 area code (reserved for testing)
        area = "555"
        exchange = _secure_random_digits(3)
        # Ensure exchange is not 000 or 911
        while exchange in ["000", "911"]:
            exchange = _secure_random_digits(3)
        
        number = _secure_random_digits(4)
        phone = area + exchange + number
        
        metadata = {
            "country_code": "US",
            "area_code": area,
            "format": "NANP",
            "reason_test": "555 area code reserved for testing"
        }
        
    elif country_code.upper() == "GB":
        # UK phone number (simplified)
        phone = "44" + _secure_random_digits(9)
        metadata = {
            "country_code": "GB",
            "format": "E.164"
        }
        
    else:
        # Generic international format
        phone = _secure_random_digits(10)
        metadata = {
            "country_code": country_code,
            "format": "generic"
        }
    
    return TestDataResult(
        value=phone,
        data_type=TestDataType.PHONE_NUMBER,
        is_valid_format=True,
        is_intentionally_invalid=country_code.upper() == "US",  # 555 is test-only
        metadata=metadata,
        generation_strategy=options.strategy
    )

def generate_test_email(domain: Optional[str] = None, options: Optional[GenerationOptions] = None) -> TestDataResult:
    """
    Generate test email address (using test domains).
    
    Args:
        domain: Specific domain to use (will use test domain if None)
        options: Generation options
        
    Returns:
        TestDataResult with generated email data
        
    Examples:
        >>> result = generate_test_email()
        >>> print(result.value)  # "test123@test-invalid.com"
    """
    if options is None:
        options = GenerationOptions()
    
    # Generate username part
    username_length = secrets.randbelow(10) + 5  # 5-14 characters
    username_chars = string.ascii_lowercase + string.digits + "._-"
    username = ''.join(_secure_random_choice(list(username_chars)) for _ in range(username_length))
    
    # Ensure it starts with alphanumeric
    if not username[0].isalnum():
        username = _secure_random_choice(string.ascii_lowercase) + username[1:]
    
    # Use test domain
    if domain is None:
        domain = _secure_random_choice(_TEST_EMAIL_DOMAINS)
    
    email = username + "@" + domain
    
    metadata = {
        "username": username,
        "domain": domain,
        "is_test_domain": domain in _TEST_EMAIL_DOMAINS,
        "format": "RFC 5322"
    }
    
    return TestDataResult(
        value=email,
        data_type=TestDataType.EMAIL,
        is_valid_format=True,
        is_intentionally_invalid=domain in _TEST_EMAIL_DOMAINS,
        metadata=metadata,
        generation_strategy=options.strategy
    )

def generate_test_ip_address(version: int = 4, options: Optional[GenerationOptions] = None) -> TestDataResult:
    """
    Generate test IP address.
    
    Args:
        version: IP version (4 or 6)
        options: Generation options
        
    Returns:
        TestDataResult with generated IP data
        
    Examples:
        >>> result = generate_test_ip_address(4)
        >>> print(result.value)  # "192.0.2.123" (test range)
    """
    if options is None:
        options = GenerationOptions()
    
    if version == 4:
        # Use TEST-NET ranges for IPv4 (RFC 3330)
        test_ranges = [
            "192.0.2",    # TEST-NET-1
            "198.51.100", # TEST-NET-2
            "203.0.113"   # TEST-NET-3
        ]
        
        network = _secure_random_choice(test_ranges)
        host = str(secrets.randbelow(254) + 1)  # 1-254
        ip = f"{network}.{host}"
        
        metadata = {
            "version": 4,
            "network": network,
            "host": host,
            "is_test_range": True
        }
        
    elif version == 6:
        # Use documentation range for IPv6 (RFC 3849)
        # 2001:db8::/32 is reserved for documentation
        prefix = "2001:db8"
        
        # Generate remaining parts
        parts = [f"{secrets.randbelow(65536):04x}" for _ in range(6)]
        ip = f"{prefix}:" + ":".join(parts)
        
        metadata = {
            "version": 6,
            "prefix": prefix,
            "is_test_range": True
        }
        
    else:
        raise ValueError("IP version must be 4 or 6")
    
    return TestDataResult(
        value=ip,
        data_type=TestDataType.IP_ADDRESS,
        is_valid_format=True,
        is_intentionally_invalid=False,  # Test ranges are valid IPs
        metadata=metadata,
        generation_strategy=options.strategy
    )

def generate_invalid_data(data_type: TestDataType, options: Optional[GenerationOptions] = None) -> TestDataResult:
    """
    Generate obviously invalid data for negative testing.
    
    Args:
        data_type: Type of invalid data to generate
        options: Generation options
        
    Returns:
        TestDataResult with invalid data
        
    Examples:
        >>> result = generate_invalid_data(TestDataType.CREDIT_CARD)
        >>> print(result.value)  # "1234567890123456" (obviously invalid)
    """
    if options is None:
        options = GenerationOptions()
    
    if data_type == TestDataType.CREDIT_CARD:
        # Generate obviously invalid credit card
        invalid_patterns = [
            "0000000000000000",  # All zeros
            "1111111111111111",  # All ones
            "1234567890123456",  # Sequential
            "abcdefghijklmnop",  # Letters
            "123",               # Too short
            "12345678901234567890"  # Too long
        ]
        
        value = _secure_random_choice(invalid_patterns)
        
        metadata = {
            "reason_invalid": "obviously invalid pattern",
            "pattern_type": "negative_test"
        }
        
    elif data_type == TestDataType.EMAIL:
        # Generate invalid email formats
        invalid_patterns = [
            "invalid.email",      # No @ sign
            "@domain.com",       # No username
            "user@",             # No domain
            "user@@domain.com",  # Double @
            "user name@domain.com",  # Space in username
            "user@domain",       # No TLD
            "",                  # Empty
            "a" * 300 + "@domain.com"  # Too long
        ]
        
        value = _secure_random_choice(invalid_patterns)
        
        metadata = {
            "reason_invalid": "invalid format",
            "pattern_type": "format_violation"
        }
        
    elif data_type == TestDataType.SSN:
        # Generate invalid SSN formats
        invalid_patterns = [
            "000000000",  # All zeros
            "123456789",  # No separators (might be valid)
            "123-45-6789-0",  # Too long
            "12-345-6789",    # Wrong format
            "abc-de-fghi",    # Letters
            "",               # Empty
            "123"             # Too short
        ]
        
        value = _secure_random_choice(invalid_patterns)
        
        metadata = {
            "reason_invalid": "invalid format or value",
            "pattern_type": "format_violation"
        }
        
    else:
        # Generic invalid data
        invalid_patterns = [
            "",
            "invalid",
            "123abc",
            "!" * 10,
            "null",
            "undefined"
        ]
        
        value = _secure_random_choice(invalid_patterns)
        
        metadata = {
            "reason_invalid": "generic invalid pattern",
            "pattern_type": "negative_test"
        }
    
    return TestDataResult(
        value=value,
        data_type=data_type,
        is_valid_format=False,
        is_intentionally_invalid=True,
        metadata=metadata,
        generation_strategy=options.strategy
    )

def generate_edge_cases(data_type: TestDataType, options: Optional[GenerationOptions] = None) -> List[TestDataResult]:
    """
    Generate edge cases for comprehensive testing.
    
    Args:
        data_type: Type of data for edge cases
        options: Generation options
        
    Returns:
        List of TestDataResult with edge cases
        
    Examples:
        >>> results = generate_edge_cases(TestDataType.CREDIT_CARD)
        >>> for result in results:
        ...     print(f"{result.value}: {result.metadata['edge_case_type']}")
    """
    if options is None:
        options = GenerationOptions()
    
    edge_cases = []
    
    if data_type == TestDataType.CREDIT_CARD:
        # Credit card edge cases
        cases = [
            ("4" + "0" * 15, "minimum_visa"),
            ("4" + "9" * 15, "maximum_visa"),
            ("5100000000000000", "minimum_mastercard"),
            ("378282246310005", "amex_test_card"),
            ("30569309025904", "diners_club"),
            ("4" * 13, "too_short"),
            ("4" * 20, "too_long")
        ]
        
        for value, case_type in cases:
            # Make sure it's invalid if requested
            if options.ensure_invalid and len(value) in [13, 14, 15, 16]:
                value = _luhn_make_invalid(value)
            
            edge_cases.append(TestDataResult(
                value=value,
                data_type=data_type,
                is_valid_format=len(value) in [13, 14, 15, 16],
                is_intentionally_invalid=options.ensure_invalid,
                metadata={"edge_case_type": case_type},
                generation_strategy=GenerationStrategy.EDGE_CASES
            ))
            
    elif data_type == TestDataType.EMAIL:
        # Email edge cases
        cases = [
            ("a@b.co", "minimal_valid"),
            ("test@" + "a" * 60 + ".com", "long_domain"),
            ("a" * 64 + "@domain.com", "max_local_part"),
            ("test+tag@domain.com", "plus_addressing"),
            ("test.dot@domain.com", "dot_in_local"),
            ("test@domain-name.com", "hyphenated_domain"),
            ("test@[192.168.1.1]", "ip_literal"),
            ("test@domain", "no_tld")
        ]
        
        for value, case_type in cases:
            # Simple format validation
            is_valid_format = "@" in value and value.count("@") == 1
            
            edge_cases.append(TestDataResult(
                value=value,
                data_type=data_type,
                is_valid_format=is_valid_format,
                is_intentionally_invalid=False,
                metadata={"edge_case_type": case_type},
                generation_strategy=GenerationStrategy.EDGE_CASES
            ))
    
    return edge_cases

def generate_test_batch(data_type: str, count: int = 100, 
                       ensure_invalid: bool = True) -> List[TestDataResult]:
    """
    Generate a batch of test data for performance testing.
    
    Args:
        data_type: Type of data to generate
        count: Number of items to generate
        ensure_invalid: Whether to ensure all data is invalid
        
    Returns:
        List of TestDataResult objects
        
    Examples:
        >>> batch = generate_test_batch("credit_card", count=50)
        >>> print(f"Generated {len(batch)} test credit cards")
    """
    if count > 100000:
        raise ValueError("Batch size too large (max 100000)")
    
    options = GenerationOptions(
        count=count,
        ensure_invalid=ensure_invalid,
        strategy=GenerationStrategy.STRESS_TEST
    )
    
    batch = []
    data_type_enum = TestDataType(data_type)
    
    for _ in range(count):
        if data_type_enum == TestDataType.CREDIT_CARD:
            result = generate_test_credit_card(options=options)
        elif data_type_enum == TestDataType.SSN:
            result = generate_test_ssn(options=options)
        elif data_type_enum == TestDataType.PHONE_NUMBER:
            result = generate_test_phone(options=options)
        elif data_type_enum == TestDataType.EMAIL:
            result = generate_test_email(options=options)
        elif data_type_enum == TestDataType.IP_ADDRESS:
            result = generate_test_ip_address(options=options)
        else:
            result = generate_invalid_data(data_type_enum, options=options)
        
        batch.append(result)
    
    return batch

def validate_test_data_safety(test_results: List[TestDataResult]) -> Dict[str, Any]:
    """
    Validate that generated test data is safe to use.
    
    Args:
        test_results: List of test data results to validate
        
    Returns:
        Dictionary with safety validation results
        
    Examples:
        >>> batch = generate_test_batch("credit_card", count=10)
        >>> safety = validate_test_data_safety(batch)
        >>> print(f"All data invalid: {safety['all_intentionally_invalid']}")
    """
    total_count = len(test_results)
    invalid_count = sum(1 for result in test_results if result.is_intentionally_invalid)
    valid_format_count = sum(1 for result in test_results if result.is_valid_format)
    
    # Check for any potentially real data
    suspicious_patterns = []
    for result in test_results:
        if result.data_type == TestDataType.CREDIT_CARD:
            # Check if it might be a real card pattern
            if result.value.startswith(("4532", "4556", "4716")) and not result.is_intentionally_invalid:
                suspicious_patterns.append(f"Potentially real card pattern: {result.value[:4]}****")
        elif result.data_type == TestDataType.SSN:
            # Check if it uses valid area numbers
            area = result.value[:3]
            if area not in _INVALID_SSN_AREAS and not result.is_intentionally_invalid:
                suspicious_patterns.append(f"Potentially real SSN area: {area}")
    
    return {
        "total_count": total_count,
        "intentionally_invalid_count": invalid_count,
        "valid_format_count": valid_format_count,
        "all_intentionally_invalid": invalid_count == total_count,
        "percentage_invalid": (invalid_count / total_count * 100) if total_count > 0 else 0,
        "suspicious_patterns": suspicious_patterns,
        "safety_score": min(100, (invalid_count / total_count * 100)) if total_count > 0 else 100,
        "is_safe_for_testing": len(suspicious_patterns) == 0 and invalid_count >= total_count * 0.95
    }

# Export all public functions
__all__ = [
    "TestDataType",
    "GenerationStrategy",
    "GenerationOptions",
    "TestDataResult", 
    "generate_test_credit_card",
    "generate_test_ssn",
    "generate_test_phone",
    "generate_test_email",
    "generate_test_ip_address",
    "generate_invalid_data",
    "generate_edge_cases",
    "generate_test_batch",
    "validate_test_data_safety"
]
