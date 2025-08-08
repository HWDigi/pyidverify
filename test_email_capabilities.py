#!/usr/bin/env python3
"""
Email Validator Capabilities Test
=================================

This script demonstrates the full capabilities of the PyIDVerify email validator,
including format checking, MX record verification, and disposable email detection.
"""

import sys
import traceback
from pathlib import Path

def test_email_validator_capabilities():
    """Test email validator with all available features"""
    print("=" * 70)
    print("EMAIL VALIDATOR CAPABILITIES TEST")
    print("=" * 70)
    
    try:
        print("Step 1: Importing email validator...")
        from pyidverify.validators.personal.email import EmailValidator
        print("✅ Email validator imported successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import email validator: {e}")
        return False
    
    # Test different validation levels
    test_configs = [
        {
            "name": "Basic Format Only", 
            "config": {"check_mx": False, "check_disposable": False},
            "description": "Only checks email format/syntax (RFC 5322)"
        },
        {
            "name": "Format + MX Records", 
            "config": {"check_mx": True, "check_disposable": False},
            "description": "Checks format AND verifies domain has mail servers"
        },
        {
            "name": "Format + Disposable Detection", 
            "config": {"check_mx": False, "check_disposable": True},
            "description": "Checks format AND detects temporary/disposable emails"
        },
        {
            "name": "Full Validation", 
            "config": {"check_mx": True, "check_disposable": True, "check_domain_reputation": True},
            "description": "All checks: format, MX records, disposable detection, domain reputation"
        }
    ]
    
    test_emails = [
        ("user@gmail.com", "Valid Gmail address"),
        ("test@example.com", "Valid format, may not have MX records"),
        ("invalid-email", "Invalid format"),
        ("user@10minutemail.com", "Disposable email service"),
        ("test@temp-mail.org", "Another disposable email"),
        ("user@nonexistent-domain-12345.com", "Non-existent domain"),
        ("admin@google.com", "Valid format, real domain")
    ]
    
    for config in test_configs:
        print(f"\n{'='*70}")
        print(f"Testing: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"{'='*70}")
        
        try:
            validator = EmailValidator(**config['config'])
            print(f"✅ Validator created with config: {config['config']}")
            
            for email, description in test_emails:
                try:
                    print(f"\nTesting: {email} ({description})")
                    result = validator.validate(email)
                    
                    print(f"  Valid: {result.is_valid}")
                    print(f"  Confidence: {result.confidence:.3f}")
                    
                    if result.errors:
                        print(f"  Errors: {result.errors}")
                    
                    # Show relevant metadata
                    relevant_meta = {}
                    if 'checks_performed' in result.metadata:
                        relevant_meta['checks_performed'] = result.metadata['checks_performed']
                    if 'mx_valid' in result.metadata:
                        relevant_meta['mx_valid'] = result.metadata['mx_valid']
                    if 'is_disposable' in result.metadata:
                        relevant_meta['is_disposable'] = result.metadata['is_disposable']
                    if 'reputation_score' in result.metadata:
                        relevant_meta['reputation_score'] = result.metadata['reputation_score']
                    
                    if relevant_meta:
                        print(f"  Metadata: {relevant_meta}")
                        
                except Exception as e:
                    print(f"  ❌ Error validating {email}: {e}")
                    
        except Exception as e:
            print(f"❌ Failed to create validator with config {config['config']}: {e}")
    
    return True

def show_email_validator_features():
    """Show what features the email validator supports"""
    print("\n" + "=" * 70)
    print("EMAIL VALIDATOR FEATURE SUMMARY")
    print("=" * 70)
    
    print("""
🎯 WHAT THE EMAIL VALIDATOR CAN DO:

1. FORMAT VALIDATION (Always Enabled):
   ✅ RFC 5322 compliance checking
   ✅ Syntax validation (proper @ placement, valid characters)
   ✅ Length validation (max 254 characters)
   ✅ Local and domain part validation
   
2. MX RECORD VERIFICATION (Optional - check_mx=True):
   🌐 Queries DNS to verify domain has mail servers
   🌐 Checks both MX records and A records (fallback)
   🌐 Confirms domain can actually receive emails
   🌐 Uses DNS caching for performance
   
3. DISPOSABLE EMAIL DETECTION (Optional - check_disposable=True):
   🗑️  Detects temporary/throwaway email services
   🗑️  Built-in database of known disposable domains
   🗑️  Can load external disposable domain lists
   🗑️  Examples: 10minutemail.com, temp-mail.org, guerrillamail.com
   
4. DOMAIN REPUTATION CHECKING (Optional - check_domain_reputation=True):
   📊 Analyzes domain reputation scores
   📊 Flags domains with poor sending reputation
   📊 Helps identify potential spam sources
   
5. SECURITY FEATURES (Always Active):
   🔒 Input sanitization and XSS protection
   🔒 Rate limiting to prevent abuse
   🔒 DNS query timeouts to prevent DoS
   🔒 Audit logging for compliance
   🔒 Memory-safe string operations

⚙️ DEFAULT BEHAVIOR (when you call EmailValidator()):
   - ✅ Format validation: ENABLED
   - ❌ MX record check: DISABLED (for performance)
   - ❌ Disposable check: DISABLED
   - ❌ Reputation check: DISABLED
   
   So by default, it only checks email FORMAT, not if the email actually exists!

🚀 TO ENABLE FULL VALIDATION:
   validator = EmailValidator(
       check_mx=True,           # Verify domain has mail servers
       check_disposable=True,   # Detect throwaway emails
       check_domain_reputation=True  # Check domain reputation
   )

📝 ANSWER TO YOUR QUESTION:
   By default, the email validator ONLY checks format (syntax).
   To verify if an email can actually receive mail, you need:
   check_mx=True (verifies domain has mail servers)
   
   This doesn't check if the specific email ADDRESS exists, but verifies
   the DOMAIN can receive emails. Full email verification would require
   SMTP probing, which is more invasive and often blocked.
""")

def main():
    """Main test function"""
    print("PyIDVerify Email Validator Capabilities Test")
    print(f"Python version: {sys.version}")
    
    # Show feature overview first
    show_email_validator_features()
    
    # Run capability tests
    success = test_email_validator_capabilities()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if success:
        print("✅ Email validator capabilities test completed successfully!")
        print("\n🎯 KEY TAKEAWAY:")
        print("   - Default behavior: Format checking only")
        print("   - For service verification: Use check_mx=True")
        print("   - For disposable detection: Use check_disposable=True")
        print("   - For full validation: Enable all options")
        return 0
    else:
        print("❌ Email validator test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
