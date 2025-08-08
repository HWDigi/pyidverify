"""
PyIDVerify Core Exceptions Module
=================================

Defines custom exceptions used throughout the PyIDVerify library.
"""


class PyIDVerifyError(Exception):
    """Base exception class for PyIDVerify."""
    pass


class ValidationError(PyIDVerifyError):
    """Raised when validation fails due to invalid input or configuration."""
    pass


class SecurityError(PyIDVerifyError):
    """Raised when a security-related issue is detected."""
    pass


class ConfigurationError(PyIDVerifyError):
    """Raised when there's a configuration problem."""
    pass


class NetworkError(PyIDVerifyError):
    """Raised when network operations fail."""
    pass


__all__ = [
    "PyIDVerifyError",
    "ValidationError", 
    "SecurityError",
    "ConfigurationError",
    "NetworkError"
]
