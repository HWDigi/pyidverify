"""
PyIDVerify Validators Package
============================

This package contains all the ID validation implementations for the PyIDVerify library.
The validators are organized by category and provide comprehensive validation for various
types of identification data.

Validator Categories:
- Personal: Email addresses, phone numbers, IP addresses  
- Financial: Credit cards, bank accounts, IBANs
- Government: SSNs, driver's licenses, passports

All validators inherit from the BaseValidator class and implement the security-first
validation framework with comprehensive audit logging and compliance features.

Examples:
    >>> from pyidverify.validators.personal import EmailValidator
    >>> from pyidverify.validators.financial import CreditCardValidator  
    >>> from pyidverify.validators.government import SSNValidator
    >>> 
    >>> # Email validation
    >>> email_validator = EmailValidator()
    >>> result = email_validator.validate("user@example.com")
    >>> print(result.is_valid)  # True
    >>> 
    >>> # Credit card validation
    >>> cc_validator = CreditCardValidator()
    >>> result = cc_validator.validate("4111111111111111")
    >>> print(result.is_valid)  # True
    >>> 
    >>> # SSN validation
    >>> ssn_validator = SSNValidator()
    >>> result = ssn_validator.validate("123-45-6789")
    >>> print(result.metadata.get('state'))  # State info

Security Features:
- All validators implement security-first design
- Comprehensive audit logging for sensitive operations
- Rate limiting and abuse prevention
- Memory-safe operations with sensitive data clearing
- Input sanitization and injection prevention
"""

from typing import Dict, Any, List, Optional, Type, Union
import sys
from pathlib import Path

# Version information
__version__ = "1.0.0-dev"
__author__ = "PyIDVerify Development Team"
__license__ = "MIT"

# Import sub-packages with graceful error handling
try:
    from . import personal
    _PERSONAL_AVAILABLE = True
except ImportError as e:
    _PERSONAL_AVAILABLE = False
    _PERSONAL_ERROR = str(e)

try:
    from . import financial
    _FINANCIAL_AVAILABLE = True
except ImportError as e:
    _FINANCIAL_AVAILABLE = False
    _FINANCIAL_ERROR = str(e)

try:
    from . import government
    _GOVERNMENT_AVAILABLE = True
except ImportError as e:
    _GOVERNMENT_AVAILABLE = False
    _GOVERNMENT_ERROR = str(e)

# Import core validator types and base classes
try:
    from pyidverify.core.base_validator import BaseValidator
    from pyidverify.core.types import IDType, ValidationResult, ValidationLevel
    from pyidverify.core.exceptions import ValidationError, SecurityError
    _CORE_AVAILABLE = True
except ImportError as e:
    _CORE_AVAILABLE = False
    _CORE_ERROR = str(e)
    
    # Fallback definitions
    class BaseValidator:
        def __init__(self): pass
        def validate(self, value): pass
    
    class IDType:
        EMAIL = "email"
        PHONE = "phone"
        IP_ADDRESS = "ip_address"
        CREDIT_CARD = "credit_card"
        SSN = "ssn"
    
    class ValidationResult:
        def __init__(self, is_valid=False, confidence=0.0, metadata=None):
            self.is_valid = is_valid
            self.confidence = confidence
            self.metadata = metadata or {}
    
    class ValidationLevel:
        BASIC = 1
        STANDARD = 2 
        STRICT = 3

# Import validator implementations
try:
    # Personal validators
    from .personal.email import EmailValidator
    from .personal.phone import PhoneValidator
    from .personal.ip_address import IPAddressValidator
    
    # Financial validators
    from .financial.credit_card import CreditCardValidator
    from .financial.bank_account import BankAccountValidator
    from .financial.iban import IBANValidator
    
    # Government validators
    from .government.ssn import SSNValidator
    from .government.drivers_license import DriversLicenseValidator
    from .government.passport import PassportValidator
    
    _VALIDATORS_AVAILABLE = True
    
except ImportError as e:
    # Graceful degradation if some validators aren't available
    _VALIDATORS_AVAILABLE = False
    _VALIDATORS_ERROR = str(e)

# Validator registry mapping
VALIDATOR_REGISTRY: Dict[IDType, Type[BaseValidator]] = {}
VALIDATOR_CATEGORIES: Dict[str, List[IDType]] = {
    "personal": [],
    "financial": [],
    "government": []
}

def _initialize_registry():
    """Initialize the validator registry with available validators"""
    if not _VALIDATORS_AVAILABLE or not _CORE_AVAILABLE:
        return
    
    try:
        # Personal validators
        VALIDATOR_REGISTRY[IDType.EMAIL] = EmailValidator
        VALIDATOR_REGISTRY[IDType.PHONE] = PhoneValidator  
        VALIDATOR_REGISTRY[IDType.IP_ADDRESS] = IPAddressValidator
        
        # Financial validators
        VALIDATOR_REGISTRY[IDType.CREDIT_CARD] = CreditCardValidator
        VALIDATOR_REGISTRY[IDType.BANK_ACCOUNT] = BankAccountValidator
        VALIDATOR_REGISTRY[IDType.IBAN] = IBANValidator
        
        # Government validators
        VALIDATOR_REGISTRY[IDType.SSN] = SSNValidator
        VALIDATOR_REGISTRY[IDType.DRIVERS_LICENSE] = DriversLicenseValidator
        VALIDATOR_REGISTRY[IDType.PASSPORT] = PassportValidator
        
        # Populate categories
        VALIDATOR_CATEGORIES["personal"] = [IDType.EMAIL, IDType.PHONE, IDType.IP_ADDRESS]
        VALIDATOR_CATEGORIES["financial"] = [IDType.CREDIT_CARD, IDType.BANK_ACCOUNT, IDType.IBAN]
        VALIDATOR_CATEGORIES["government"] = [IDType.SSN, IDType.DRIVERS_LICENSE, IDType.PASSPORT]
        
    except Exception as e:
        print(f"Warning: Failed to initialize validator registry: {e}")

# Initialize registry on import
_initialize_registry()

def get_validator(id_type: Union[IDType, str]) -> Optional[BaseValidator]:
    """
    Get validator instance for the specified ID type.
    
    Args:
        id_type: Type of ID to validate (IDType enum or string)
        
    Returns:
        Validator instance or None if not available
        
    Raises:
        ValidationError: If validator type is not supported
        
    Examples:
        >>> validator = get_validator(IDType.EMAIL)
        >>> result = validator.validate("user@example.com")
        >>> 
        >>> validator = get_validator("credit_card")
        >>> result = validator.validate("4532015112830366")
    """
    if not _VALIDATORS_AVAILABLE or not _CORE_AVAILABLE:
        raise ValidationError(f"Validators not available: {_VALIDATORS_ERROR if _VALIDATORS_AVAILABLE else _CORE_ERROR}")
    
    # Convert string to IDType if needed
    if isinstance(id_type, str):
        try:
            id_type = IDType(id_type)
        except ValueError:
            raise ValidationError(f"Unknown ID type: {id_type}")
    
    if id_type not in VALIDATOR_REGISTRY:
        raise ValidationError(f"No validator available for ID type: {id_type.value}")
    
    validator_class = VALIDATOR_REGISTRY[id_type]
    return validator_class()

def get_available_validators() -> List[str]:
    """
    Get list of available validator types.
    
    Returns:
        List of available validator type names
        
    Examples:
        >>> validators = get_available_validators()
        >>> print(validators)
        ['email', 'phone', 'credit_card', 'ssn', ...]
    """
    if not _VALIDATORS_AVAILABLE or not _CORE_AVAILABLE:
        return []
    
    return [id_type.value for id_type in VALIDATOR_REGISTRY.keys()]

def get_validators_by_category(category: str) -> List[str]:
    """
    Get validators in a specific category.
    
    Args:
        category: Category name ("personal", "financial", "government")
        
    Returns:
        List of validator types in the category
        
    Examples:
        >>> personal = get_validators_by_category("personal")
        >>> print(personal)
        ['email', 'phone', 'ip_address']
    """
    if not _VALIDATORS_AVAILABLE or not _CORE_AVAILABLE:
        return []
    
    if category not in VALIDATOR_CATEGORIES:
        return []
    
    return [id_type.value for id_type in VALIDATOR_CATEGORIES[category]]

def validate_id(value: str, id_type: Union[IDType, str], **kwargs) -> ValidationResult:
    """
    Convenience function to validate an ID value.
    
    Args:
        value: ID value to validate
        id_type: Type of ID to validate
        **kwargs: Additional validation options
        
    Returns:
        ValidationResult with validation details
        
    Raises:
        ValidationError: If validation fails or validator not available
        
    Examples:
        >>> result = validate_id("user@example.com", "email")
        >>> print(f"Valid: {result.is_valid}")
        >>> 
        >>> result = validate_id("4532015112830366", IDType.CREDIT_CARD)
        >>> print(f"Card type: {result.metadata.get('card_type')}")
    """
    validator = get_validator(id_type)
    return validator.validate(value, **kwargs)

def validate_batch(values: List[str], id_type: Union[IDType, str], 
                  **kwargs) -> List[ValidationResult]:
    """
    Validate multiple ID values of the same type.
    
    Args:
        values: List of ID values to validate
        id_type: Type of ID to validate
        **kwargs: Additional validation options
        
    Returns:
        List of ValidationResult objects
        
    Examples:
        >>> emails = ["user1@test.com", "user2@example.com", "invalid-email"]
        >>> results = validate_batch(emails, "email")
        >>> valid_count = sum(1 for r in results if r.is_valid)
    """
    validator = get_validator(id_type)
    return validator.validate_batch(values, **kwargs)

def create_validator_from_config(config: Dict[str, Any]) -> BaseValidator:
    """
    Create validator instance from configuration.
    
    Args:
        config: Validator configuration dictionary
        
    Returns:
        Configured validator instance
        
    Raises:
        ValidationError: If configuration is invalid
        
    Examples:
        >>> config = {
        ...     "type": "email",
        ...     "check_mx": True,
        ...     "check_disposable": True
        ... }
        >>> validator = create_validator_from_config(config)
    """
    if "type" not in config:
        raise ValidationError("Validator configuration must specify 'type'")
    
    validator = get_validator(config["type"])
    
    # Apply configuration options
    if hasattr(validator, 'configure'):
        validator.configure(config)
    
    return validator

def get_validator_info(id_type: Union[IDType, str]) -> Dict[str, Any]:
    """
    Get information about a specific validator.
    
    Args:
        id_type: Type of ID validator to get info for
        
    Returns:
        Dictionary with validator information
        
    Examples:
        >>> info = get_validator_info("email")
        >>> print(info["description"])
    """
    if not _VALIDATORS_AVAILABLE or not _CORE_AVAILABLE:
        return {"error": "Validators not available"}
    
    # Convert string to IDType if needed
    if isinstance(id_type, str):
        try:
            id_type = IDType(id_type)
        except ValueError:
            return {"error": f"Unknown ID type: {id_type}"}
    
    if id_type not in VALIDATOR_REGISTRY:
        return {"error": f"No validator available for ID type: {id_type.value}"}
    
    validator_class = VALIDATOR_REGISTRY[id_type]
    
    info = {
        "id_type": id_type.value,
        "class_name": validator_class.__name__,
        "module": validator_class.__module__,
        "category": None,
        "description": validator_class.__doc__ or "No description available"
    }
    
    # Find category
    for category, types in VALIDATOR_CATEGORIES.items():
        if id_type in types:
            info["category"] = category
            break
    
    # Get additional info if validator has it
    if hasattr(validator_class, 'get_info'):
        try:
            validator = validator_class()
            additional_info = validator.get_info()
            info.update(additional_info)
        except Exception:
            pass  # Ignore errors getting additional info
    
    return info

def benchmark_validators(iterations: int = 1000) -> Dict[str, Any]:
    """
    Benchmark performance of all available validators.
    
    Args:
        iterations: Number of test iterations per validator
        
    Returns:
        Dictionary with benchmark results
        
    Examples:
        >>> results = benchmark_validators(100)
        >>> for validator_type, metrics in results.items():
        ...     print(f"{validator_type}: {metrics['avg_time_ms']:.2f}ms")
    """
    if not _VALIDATORS_AVAILABLE or not _CORE_AVAILABLE:
        return {"error": "Validators not available"}
    
    import time
    from ..utils.generators import generate_test_data
    
    results = {}
    
    for id_type in VALIDATOR_REGISTRY.keys():
        try:
            validator = get_validator(id_type)
            
            # Generate test data
            test_values = []
            for _ in range(iterations):
                if id_type == IDType.EMAIL:
                    test_values.append("test@example.com")
                elif id_type == IDType.PHONE:
                    test_values.append("5551234567")
                elif id_type == IDType.CREDIT_CARD:
                    test_values.append("4532015112830366")
                elif id_type == IDType.SSN:
                    test_values.append("123456789")
                else:
                    test_values.append("test_value_123")
            
            # Benchmark validation
            start_time = time.perf_counter()
            
            for value in test_values:
                try:
                    validator.validate(value)
                except Exception:
                    pass  # Ignore validation errors during benchmarking
            
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            avg_time = (total_time / iterations) * 1000  # Convert to milliseconds
            
            results[id_type.value] = {
                "iterations": iterations,
                "total_time_s": total_time,
                "avg_time_ms": avg_time,
                "operations_per_second": iterations / total_time if total_time > 0 else 0
            }
            
        except Exception as e:
            results[id_type.value] = {"error": str(e)}
    
    return results

def get_package_info() -> Dict[str, Any]:
    """
    Get information about the validators package.
    
    Returns:
        Dictionary containing package information
        
    Examples:
        >>> info = get_package_info()
        >>> print(f"Available validators: {info['validator_count']}")
    """
    return {
        "version": __version__,
        "core_available": _CORE_AVAILABLE,
        "validators_available": _VALIDATORS_AVAILABLE,
        "core_error": _CORE_ERROR if not _CORE_AVAILABLE else None,
        "validators_error": _VALIDATORS_ERROR if not _VALIDATORS_AVAILABLE else None,
        "validator_count": len(VALIDATOR_REGISTRY),
        "available_validators": list(VALIDATOR_REGISTRY.keys()) if _VALIDATORS_AVAILABLE else [],
        "categories": list(VALIDATOR_CATEGORIES.keys()),
        "registry_initialized": len(VALIDATOR_REGISTRY) > 0
    }

# Export all public functions and classes
def get_available_validator_packages():
    """
    Get available validator packages and their status.
    
    Returns:
        Dictionary with package availability information
    """
    return {
        'personal': {
            'available': _PERSONAL_AVAILABLE,
            'error': _PERSONAL_ERROR if not _PERSONAL_AVAILABLE else None,
            'validators': personal.list_personal_validators() if _PERSONAL_AVAILABLE else {}
        },
        'financial': {
            'available': _FINANCIAL_AVAILABLE,
            'error': _FINANCIAL_ERROR if not _FINANCIAL_AVAILABLE else None,
            'validators': financial.list_financial_validators() if _FINANCIAL_AVAILABLE else {}
        },
        'government': {
            'available': _GOVERNMENT_AVAILABLE,
            'error': _GOVERNMENT_ERROR if not _GOVERNMENT_AVAILABLE else None,
            'validators': government.list_government_validators() if _GOVERNMENT_AVAILABLE else {}
        }
    }

def get_all_validators():
    """
    Get all available validators from all packages.
    
    Returns:
        Dictionary with all validator information
    """
    all_validators = {}
    
    if _PERSONAL_AVAILABLE:
        try:
            all_validators.update({
                f"personal.{k}": v 
                for k, v in personal.list_personal_validators().items()
            })
        except Exception:
            pass
    
    if _FINANCIAL_AVAILABLE:
        try:
            all_validators.update({
                f"financial.{k}": v 
                for k, v in financial.list_financial_validators().items()
            })
        except Exception:
            pass
    
    if _GOVERNMENT_AVAILABLE:
        try:
            all_validators.update({
                f"government.{k}": v 
                for k, v in government.list_government_validators().items()
            })
        except Exception:
            pass
    
    return all_validators

def create_validator_by_name(validator_name: str, **options):
    """
    Create validator by full name (package.type format).
    
    Args:
        validator_name: Full validator name (e.g., "personal.email", "financial.credit_card")
        **options: Configuration options for the validator
        
    Returns:
        Configured validator instance
        
    Raises:
        ValueError: If validator is not found or package not available
    """
    if '.' not in validator_name:
        raise ValueError("Validator name must include package (e.g., 'personal.email')")
    
    package, validator_type = validator_name.split('.', 1)
    
    if package == 'personal' and _PERSONAL_AVAILABLE:
        return personal.create_personal_validator(validator_type, **options)
    elif package == 'financial' and _FINANCIAL_AVAILABLE:
        return financial.create_financial_validator(validator_type, **options)
    elif package == 'government' and _GOVERNMENT_AVAILABLE:
        return government.create_government_validator(validator_type, **options)
    else:
        available_packages = [k for k, v in get_available_validator_packages().items() if v['available']]
        raise ValueError(
            f"Validator '{validator_name}' not found or package not available. "
            f"Available packages: {available_packages}"
        )

def get_validators_by_category(category: str):
    """
    Get validators by category.
    
    Args:
        category: Category name ('personal', 'financial', 'government')
        
    Returns:
        Dictionary with validators in the category
    """
    category = category.lower()
    
    if category == 'personal' and _PERSONAL_AVAILABLE:
        return personal.list_personal_validators()
    elif category == 'financial' and _FINANCIAL_AVAILABLE:
        return financial.list_financial_validators()
    elif category == 'government' and _GOVERNMENT_AVAILABLE:
        return government.list_government_validators()
    else:
        return {}

def create_secure_validator(validator_name: str, **options):
    """
    Create validator with security-focused configuration.
    
    Args:
        validator_name: Full validator name
        **options: Additional configuration options
        
    Returns:
        Configured validator with security settings
    """
    if '.' not in validator_name:
        raise ValueError("Validator name must include package (e.g., 'personal.email')")
    
    package, validator_type = validator_name.split('.', 1)
    
    if package == 'personal' and _PERSONAL_AVAILABLE:
        # Use personal package secure creation if available
        if hasattr(personal, 'create_secure_validator'):
            return personal.create_secure_validator(validator_type, **options)
        else:
            return personal.create_personal_validator(validator_type, **options)
    elif package == 'financial' and _FINANCIAL_AVAILABLE:
        return financial.create_secure_validator(validator_type, **options)
    elif package == 'government' and _GOVERNMENT_AVAILABLE:
        return government.create_privacy_compliant_validator(validator_type, **options)
    else:
        raise ValueError(f"Package '{package}' not available")

def validate_package_compliance(package: str, config: dict):
    """
    Validate compliance for a validator package.
    
    Args:
        package: Package name ('financial', 'government')
        config: Validator configuration
        
    Returns:
        Dictionary with compliance status
    """
    if package == 'financial' and _FINANCIAL_AVAILABLE:
        return financial.validate_pci_compliance(config)
    elif package == 'government' and _GOVERNMENT_AVAILABLE:
        return government.validate_privacy_compliance(config)
    else:
        return {'is_compliant': False, 'error': f"Package '{package}' not available or doesn't support compliance validation"}

# Define exports
__all__ = [
    # Sub-packages
    'personal',
    'financial', 
    'government',
    
    # New utility functions
    'get_available_validator_packages',
    'get_all_validators', 
    'create_validator_by_name',
    'get_validators_by_category',
    'create_secure_validator',
    'validate_package_compliance'
]
