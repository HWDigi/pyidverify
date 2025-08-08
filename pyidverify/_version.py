"""
PyIDVerify Version Information

Contains version information and metadata for the PyIDVerify package.

Author: PyIDVerify Team
License: MIT
"""

# Version information
__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

# Package metadata
__title__ = "PyIDVerify"
__description__ = "Enterprise-grade Python library for identity document verification and validation"
__url__ = "https://github.com/pyidverify/pyidverify"
__author__ = "PyIDVerify Team"
__author_email__ = "team@pyidverify.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 PyIDVerify Team"

# Build information (updated during build process)
__build_date__ = "2025-08-07"
__git_commit__ = "unknown"
__build_number__ = "dev"

# Feature flags
FEATURES = {
    "biometric_support": False,  # Will be enabled when biometrics implemented
    "enterprise_features": True,
    "api_integration": True,
    "audit_logging": True,
    "rate_limiting": True,
    "encryption": True,
    "async_support": True,
    "batch_processing": True,
    "auto_detection": True,
    "custom_validators": True,
    "plugin_system": True,
    "monitoring": True,
    "compliance_tools": True,
}

# API version for compatibility
API_VERSION = "1.0"
API_VERSION_INFO = (1, 0)

# Minimum required versions
MIN_PYTHON_VERSION = (3, 8)
MIN_SUPPORTED_VERSIONS = {
    "cryptography": "3.4.0",
    "requests": "2.25.0",
    "pydantic": "1.8.0",
    "typing-extensions": "3.10.0",
}

# Version tuple for easy comparison
version_info = __version_info__


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_info() -> tuple:
    """Get the current version as a tuple."""
    return __version_info__


def get_full_version() -> str:
    """Get full version with build information."""
    base_version = __version__
    if __build_number != "dev":
        base_version += f".{__build_number}"
    if __git_commit != "unknown":
        base_version += f"+{__git_commit[:8]}"
    return base_version


def get_build_info() -> dict:
    """Get complete build information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "build_date": __build_date__,
        "git_commit": __git_commit__,
        "build_number": __build_number__,
        "features": FEATURES,
        "api_version": API_VERSION,
    }


def check_compatibility() -> bool:
    """Check if current environment meets minimum requirements."""
    import sys
    
    # Check Python version
    if sys.version_info < MIN_PYTHON_VERSION:
        return False
        
    # Check required packages (basic check)
    try:
        import cryptography
        import requests
        # Add other critical imports here
        return True
    except ImportError:
        return False


def print_version_info():
    """Print detailed version information."""
    info = get_build_info()
    print(f"{__title__} v{get_full_version()}")
    print(f"Build Date: {info['build_date']}")
    print(f"Git Commit: {info['git_commit']}")
    print(f"API Version: {info['api_version']}")
    print(f"Features: {', '.join(k for k, v in info['features'].items() if v)}")


if __name__ == "__main__":
    print_version_info()
