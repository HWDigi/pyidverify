# Contributing to PyIDVerify

Thank you for your interest in contributing to PyIDVerify! We welcome contributions from the community and are excited to work with you.

## 🚨 **Important Security Notice**

PyIDVerify handles sensitive personal identification data. All contributions must follow strict security and privacy guidelines:

⚠️ **NEVER use real personal data in contributions**  
⚠️ **ALWAYS use test data generators provided by the library**  
⚠️ **FOLLOW security best practices for sensitive data handling**  
⚠️ **REPORT security vulnerabilities privately to security@pyidverify.com**

## 📋 **Table of Contents**

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Security Guidelines](#security-guidelines)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Community](#community)

## 🚀 **Getting Started**

### Prerequisites

- **Python 3.8+** (Python 3.11+ recommended)
- **Git** for version control
- **Redis** (optional, for caching and rate limiting)
- **PostgreSQL** (optional, for audit logging)

### First Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/pyidverify.git
   cd pyidverify
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/pyidverify/pyidverify.git
   ```

## 🛠️ **Development Setup**

### Install Development Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install in development mode with all dependencies
pip install -e .[dev,test,all]
```

### Install Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files (optional)
pre-commit run --all-files
```

### Environment Configuration

Create a `.env` file for development:

```bash
# Security Configuration
PYIDVERIFY_SECURITY_LEVEL=development
PYIDVERIFY_ENABLE_AUDIT=true
PYIDVERIFY_LOG_LEVEL=DEBUG

# Development Settings
PYIDVERIFY_CACHE_ENABLED=false
PYIDVERIFY_RATE_LIMIT_ENABLED=false

# Test Database (optional)
PYIDVERIFY_TEST_DB_URL=postgresql://test:test@localhost/pyidverify_test
```

### Verify Installation

```bash
# Run basic tests
python -m pytest tests/unit/test_basic.py -v

# Check code quality
python -m flake8 pyidverify/
python -m mypy pyidverify/
python -m bandit -r pyidverify/

# Run security scan
python -m safety check
```

## 📝 **Contributing Guidelines**

### Types of Contributions

We welcome several types of contributions:

#### 🐛 **Bug Reports**
- Use clear, descriptive titles
- Include minimal reproduction steps
- **Never include real personal data**
- Use test data generators for examples

#### ✨ **Feature Requests**
- Describe the problem you're solving
- Explain why it's beneficial to users
- Consider security and compliance implications
- Include potential implementation approach

#### 🔧 **Code Contributions**
- Bug fixes and improvements
- New validation algorithms
- Performance optimizations
- Security enhancements
- Documentation improvements

#### 📚 **Documentation**
- API documentation improvements
- Tutorial and example updates
- Security best practices
- Compliance guides

### Contribution Workflow

1. **Check existing issues** to avoid duplication
2. **Create an issue** for discussion (for large changes)
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following our guidelines
5. **Add/update tests** for your changes
6. **Run the test suite** locally
7. **Update documentation** if needed
8. **Submit a pull request**

## 🔒 **Security Guidelines**

### Data Handling Rules

#### ✅ **Acceptable Test Data**
```python
# Use library's test data generators
from pyidverify.testing import generate_test_data

# Generate invalid SSNs for testing
test_ssns = generate_test_data('ssn', count=10, valid=False)

# Use standardized test credit cards
test_cards = [
    '4000000000000002',  # Visa test card
    '5555555555554444',  # MasterCard test card
]

# Use example.com for email tests
test_emails = [
    'test.user@example.com',
    'invalid.email@example.com',
]
```

#### ❌ **Prohibited Data**
```python
# NEVER do this in contributions
bad_ssns = ['123-45-6789']  # Real SSN format
bad_cards = ['4532-1234-5678-9012']  # Could be real
bad_emails = ['user@gmail.com']  # Real email provider
```

### Security Review Process

All contributions undergo security review:

1. **Automated security scanning** with Bandit and Safety
2. **Manual code review** by security team
3. **Data privacy assessment** for GDPR/HIPAA compliance
4. **Penetration testing** for security-critical features

### Vulnerability Reporting

Found a security issue? **DO NOT** create a public issue.

**Report privately to**: security@pyidverify.com

Include:
- Description of the vulnerability
- Steps to reproduce (without real data)
- Potential impact assessment
- Suggested remediation (if any)

## 💻 **Code Standards**

### Python Code Style

We follow **PEP 8** with some modifications:

```python
# Use type hints for all functions
def validate_ssn(ssn: str, *, strict: bool = False) -> ValidationResult:
    """Validate a Social Security Number.
    
    Args:
        ssn: The SSN to validate (test data only)
        strict: Whether to use strict validation rules
        
    Returns:
        ValidationResult with validation outcome
        
    Raises:
        ValidationError: If input format is invalid
        SecurityError: If real data is detected
    """
    pass

# Use dataclasses for structured data
@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float
    metadata: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
```

### Security-First Coding

```python
# Use constant-time comparisons for sensitive data
import hmac

def secure_compare(a: str, b: str) -> bool:
    """Compare strings in constant time."""
    return hmac.compare_digest(a.encode(), b.encode())

# Clear sensitive data from memory
def clear_sensitive_data(data: str) -> None:
    """Securely clear sensitive data from memory."""
    # Implementation depends on your security requirements
    pass

# Use secure random for cryptographic operations
import secrets

def generate_secure_token() -> str:
    """Generate cryptographically secure token."""
    return secrets.token_urlsafe(32)
```

### Error Handling

```python
from pyidverify.exceptions import ValidationError, SecurityError

# Specific exception types for different errors
class InvalidSSNFormatError(ValidationError):
    """Raised when SSN format is invalid."""
    pass

class RealDataDetectedError(SecurityError):
    """Raised when real personal data is detected."""
    pass

# Include security context in error messages
def validate_input(data: str) -> None:
    if looks_like_real_data(data):
        raise RealDataDetectedError(
            "Real personal data detected. Use test data generators instead."
        )
```

## 🧪 **Testing Requirements**

### Test Categories

1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Component interaction testing  
3. **Security Tests**: Vulnerability and attack testing
4. **Performance Tests**: Speed and throughput testing
5. **Compliance Tests**: GDPR, HIPAA, PCI DSS testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/security/
python -m pytest tests/performance/

# Run with coverage
python -m pytest --cov=pyidverify --cov-report=html

# Run security-specific tests
python -m pytest -m security
```

### Writing Tests

```python
import pytest
from pyidverify.testing import generate_test_data
from pyidverify import validate

class TestSSNValidation:
    """Test SSN validation functionality."""
    
    def test_valid_ssn_format(self):
        """Test valid SSN format recognition."""
        # Use test data generator
        test_ssns = generate_test_data('ssn', count=5, valid=False)
        
        for ssn in test_ssns:
            result = validate(ssn, 'ssn')
            # Test data should always be invalid
            assert not result.is_valid
    
    @pytest.mark.security
    def test_real_data_detection(self):
        """Test that real data is detected and rejected."""
        # This should raise SecurityError
        with pytest.raises(SecurityError):
            validate('123-45-6789', 'ssn')  # Suspicious pattern
    
    def test_timing_attack_resistance(self):
        """Test that validation time is constant."""
        import time
        
        test_data = generate_test_data('ssn', count=100, valid=False)
        times = []
        
        for ssn in test_data:
            start = time.perf_counter()
            validate(ssn, 'ssn')
            end = time.perf_counter()
            times.append(end - start)
        
        # Verify timing consistency (implementation-dependent)
        avg_time = sum(times) / len(times)
        assert all(abs(t - avg_time) < avg_time * 0.1 for t in times)
```

### Security Test Examples

```python
@pytest.mark.security
def test_injection_resistance():
    """Test SQL injection resistance."""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "<script>alert('xss')</script>",
    ]
    
    for malicious_input in malicious_inputs:
        with pytest.raises(ValidationError):
            validate(malicious_input, 'ssn')

@pytest.mark.security
def test_memory_cleanup():
    """Test that sensitive data is cleared from memory."""
    test_data = generate_test_data('ssn', count=1, valid=False)[0]
    
    # This would need implementation-specific memory checking
    validate(test_data, 'ssn')
    
    # Verify data is not in memory (implementation-dependent)
    # This is a placeholder - actual implementation would check memory
    assert_memory_cleared(test_data)
```

## 📖 **Documentation**

### Documentation Types

1. **API Documentation**: Docstrings and auto-generated docs
2. **User Guides**: How-to guides and tutorials
3. **Security Documentation**: Security best practices
4. **Compliance Guides**: GDPR, HIPAA, PCI DSS guidance

### Writing Documentation

```python
def validate_credit_card(
    card_number: str, 
    *, 
    card_type: Optional[str] = None,
    enable_luhn: bool = True
) -> ValidationResult:
    """Validate a credit card number.
    
    This function validates credit card numbers using the Luhn algorithm
    and format-specific rules. For security, only test credit card numbers
    should be used.
    
    Args:
        card_number: The credit card number to validate. Must be test data.
        card_type: Optional card type hint ('visa', 'mastercard', 'amex')
        enable_luhn: Whether to perform Luhn algorithm validation
        
    Returns:
        ValidationResult containing:
            - is_valid: Whether the card number is valid
            - confidence: Confidence score (0.0 to 1.0)
            - metadata: Additional validation information
            
    Raises:
        ValidationError: If the input format is invalid
        SecurityError: If real credit card data is detected
        
    Security:
        This function includes real data detection to prevent processing
        of actual credit card numbers. Use test card numbers only.
        
    Example:
        >>> from pyidverify.testing import get_test_card_number
        >>> test_card = get_test_card_number('visa')
        >>> result = validate_credit_card(test_card)
        >>> print(f"Valid: {result.is_valid}")
        Valid: False  # Test data is always invalid
        
    Note:
        Test credit card numbers are designed to fail validation to
        prevent accidental processing of real payment data.
    """
    pass
```

### Security Documentation

Document security considerations for all features:

```markdown
## Security Considerations

### Data Protection
- All validation functions detect and reject real personal data
- Test data generators create invalid-by-design data
- Memory is securely cleared after processing sensitive data

### Encryption
- AES-256-GCM for symmetric encryption
- Ed25519 for digital signatures
- Argon2id for password hashing

### Compliance
- GDPR Article 25 (Privacy by Design) implemented
- HIPAA security controls for healthcare data
- PCI DSS requirements for payment data

### Threat Model
- Timing attacks mitigated with constant-time operations
- SQL injection prevented with parameterized queries
- XSS prevented with input sanitization
```

## 🔄 **Pull Request Process**

### Before Submitting

1. **Rebase on latest main**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run full test suite**:
   ```bash
   python -m pytest
   python -m mypy pyidverify/
   python -m bandit -r pyidverify/
   ```

3. **Update documentation** if needed

4. **Add changelog entry** to `CHANGELOG.md`

### Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Security improvement

## Security Review
- [ ] No real personal data used in examples or tests
- [ ] Used test data generators where applicable
- [ ] Followed secure coding practices
- [ ] Updated security documentation if needed

## Testing
- [ ] Added/updated unit tests
- [ ] Added/updated integration tests
- [ ] Added security tests if applicable
- [ ] All tests pass locally

## Compliance
- [ ] Changes comply with GDPR requirements
- [ ] Changes comply with HIPAA requirements (if applicable)
- [ ] Changes comply with PCI DSS requirements (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is commented appropriately
- [ ] Documentation updated
- [ ] No breaking changes without justification
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Security review** by security team
3. **Code review** by maintainers
4. **Compliance review** if applicable
5. **Manual testing** for significant changes

### Merge Requirements

- ✅ All automated checks pass
- ✅ Security review approval
- ✅ At least one maintainer approval
- ✅ No unresolved review comments
- ✅ Documentation is updated
- ✅ Changelog entry added

## 🚀 **Release Process**

### Version Numbering

We follow **Semantic Versioning** (SemVer):

- **Major** (X.0.0): Breaking changes
- **Minor** (X.Y.0): New features, backwards compatible
- **Patch** (X.Y.Z): Bug fixes, backwards compatible

### Release Checklist

1. **Update version numbers**
2. **Update CHANGELOG.md**
3. **Run security audit**
4. **Update documentation**
5. **Create release PR**
6. **Tag release**
7. **Deploy to PyPI**
8. **Update security documentation**

### Security Releases

For security fixes:
1. **Private development** in security branch
2. **Coordinated disclosure** process
3. **Expedited review and testing**
4. **Emergency release** if critical

## 👥 **Community**

### Communication Channels

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Security Email**: security@pyidverify.com
- **Conduct Email**: conduct@pyidverify.com

### Getting Help

- **Documentation**: https://pyidverify.readthedocs.io
- **Examples**: Check `examples/` directory
- **API Reference**: Auto-generated from docstrings
- **Security Guide**: Comprehensive security documentation

### Recognition

We maintain a `CONTRIBUTORS.md` file to recognize all contributors:

- Code contributors
- Documentation contributors
- Security researchers
- Community supporters

## 📧 **Contact Information**

- **General Questions**: maintainers@pyidverify.com
- **Security Issues**: security@pyidverify.com
- **Conduct Issues**: conduct@pyidverify.com
- **Legal Questions**: legal@pyidverify.com

## 📄 **Additional Resources**

- **[Security Policy](SECURITY.md)**: Detailed security guidelines
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Community standards
- **[License](LICENSE)**: MIT with additional terms
- **[Changelog](CHANGELOG.md)**: Version history
- **[Security Documentation](docs/security/)**: Comprehensive security guide

---

**Thank you for contributing to PyIDVerify! Together we can build secure, compliant ID verification for everyone.**
