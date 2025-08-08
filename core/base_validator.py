"""
PyIDVerify Base Validator Module
================================

Provides the abstract base class for all validators in the PyIDVerify library.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .types import ValidationResult, ValidationLevel, IDType
from .exceptions import ValidationError


class BaseValidator(ABC):
    """
    Abstract base class for all PyIDVerify validators.
    
    This class defines the common interface that all validators must implement.
    """
    
    def __init__(self):
        """Initialize the base validator."""
        self._validator_info = self._create_validator_info()
    
    @abstractmethod
    def _create_validator_info(self) -> Dict[str, Any]:
        """
        Create validator information dictionary.
        
        Returns:
            Dictionary containing validator metadata
        """
        pass
    
    @abstractmethod
    def _validate_internal(self, value: Any, **kwargs) -> ValidationResult:
        """
        Internal validation method to be implemented by subclasses.
        
        Args:
            value: Value to validate
            **kwargs: Additional validation options
            
        Returns:
            ValidationResult instance
        """
        pass
    
    def validate(self, value: Any, validation_level: Optional[ValidationLevel] = None, **kwargs) -> ValidationResult:
        """
        Validate a value using this validator.
        
        Args:
            value: Value to validate
            validation_level: Level of validation to perform
            **kwargs: Additional validation options
            
        Returns:
            ValidationResult instance
            
        Raises:
            ValidationError: If validation cannot be performed
        """
        try:
            return self._validate_internal(value, validation_level=validation_level, **kwargs)
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def get_validator_info(self) -> Dict[str, Any]:
        """
        Get information about this validator.
        
        Returns:
            Dictionary containing validator metadata
        """
        return self._validator_info.copy()
    
    def get_supported_types(self) -> list:
        """
        Get list of supported ID types for this validator.
        
        Returns:
            List of supported IDType enums
        """
        return self._validator_info.get("supported_types", [])
    
    def _create_result(self, is_valid: bool, errors: list = None, 
                      metadata: Dict[str, Any] = None, confidence: float = 1.0) -> ValidationResult:
        """
        Helper method to create ValidationResult instances.
        
        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            metadata: Additional metadata
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            ValidationResult instance
        """
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            errors=errors or [],
            metadata=metadata or {}
        )


__all__ = ["BaseValidator"]
