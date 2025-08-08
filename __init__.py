# PyIDVerify Package Structure
__version__ = "2.0.0"
__author__ = "HWDigi Team"
__license__ = "MIT"

# Import main validators for easy access
try:
    # Import only validators that actually exist
    from .validators.personal.email import EmailValidator
    from .validators.government.ssn import SSNValidator
    from .validators.financial.credit_card import CreditCardValidator
    
    # Conditional import for phone validator (requires phonenumbers)
    try:
        from .validators.personal.phone import PhoneValidator
        _PHONE_AVAILABLE = True
    except ImportError:
        _PHONE_AVAILABLE = False
        PhoneValidator = None
    
    # Import core types
    from .core.types import ValidationResult, ValidationLevel, IDType
    from .core.exceptions import ValidationError, SecurityError
    
    # Build __all__ list with available components only
    __all__ = [
        # Always available validators
        "EmailValidator",
        "SSNValidator", 
        "CreditCardValidator",
        
        # Core types
        "ValidationResult",
        "ValidationLevel", 
        "IDType",
        "ValidationError",
        "SecurityError",
        
        # Package info
        "__version__",
        "__author__",
        "__email__",
        "__license__",
        
        # Utility functions
        "get_available_validators",
    ]
    
    # Add phone validator if available
    if _PHONE_AVAILABLE:
        __all__.append("PhoneValidator")
    
    def get_available_validators():
        """Return list of available validator names."""
        validators = ["EmailValidator", "SSNValidator", "CreditCardValidator"]
        if _PHONE_AVAILABLE:
            validators.append("PhoneValidator")
        return validators
    
except ImportError as e:
    # Fallback for incomplete installations
    __all__ = ["__version__", "__author__", "__email__", "__license__"]
    import warnings
    warnings.warn(f"Some PyIDVerify components could not be imported: {e}")
