"""
PyIDVerify Core Types Module
============================

Defines core data types and enums used throughout the PyIDVerify library.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


class IDType(Enum):
    """Enumeration of supported ID types."""
    EMAIL = "email"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    BANK_ACCOUNT = "bank_account"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    IBAN = "iban"
    REGEX = "regex"


class ValidationLevel(Enum):
    """Validation level enumeration."""
    BASIC = 1
    STANDARD = 2
    STRICT = 3


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    Attributes:
        is_valid: Whether the validation passed
        confidence: Confidence score (0.0 to 1.0)
        errors: List of validation errors
        metadata: Additional validation metadata
    """
    is_valid: bool
    confidence: float = 0.0
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


__all__ = ["IDType", "ValidationLevel", "ValidationResult"]
