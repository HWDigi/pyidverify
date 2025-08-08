#!/usr/bin/env python3
"""
Simple Email Validator Test
===========================

This script shows the email validator capabilities in a simple way.
"""

def test_email_validator_simple():
    """Simple test of email validator capabilities"""
    print("=" * 60)
    print("EMAIL VALIDATOR CAPABILITIES ANALYSIS")
    print("=" * 60)
    
    try:
        from pyidverify.validators.personal.email import EmailValidator
        print("✅ Email validator imported successfully")
        
        # Test 1: Default behavior (format only)
        print("\n📝 TEST 1: Default Email Validator (format checking only)")
        print("-" * 50)
        
        validator = EmailValidator()
        
        test_emails = [
            "user@gmail.com",
            "invalid-email",
            "test@example.com",
            "admin@nonexistent-domain-12345.com"
        ]
        
        for email in test_emails:
            try:
                result = validator.validate(email)
                print(f"{email:<35} → Valid: {result.is_valid}")
                if hasattr(result, 'errors') and result.errors:
                    print(f"{'':35}   Errors: {result.errors}")
            except Exception as e:
                print(f"{email:<35} → Error: {e}")
        
        # Test 2: With MX checking
        print(f"\n🌐 TEST 2: With MX Record Checking (check_mx=True)")
        print("-" * 50)
        
        try:
            validator_mx = EmailValidator(check_mx=True)
            
            mx_test_emails = [
                "user@gmail.com",      # Should have MX records
                "test@example.com",    # May not have MX records
                "user@nonexistent-domain-12345.com"  # No MX records
            ]
            
            for email in mx_test_emails:
                try:
                    result = validator_mx.validate(email)
                    print(f"{email:<35} → Valid: {result.is_valid}")
                    if hasattr(result, 'errors') and result.errors:
                        print(f"{'':35}   Errors: {result.errors}")
                        
                    # Show MX-specific metadata
                    if hasattr(result, 'metadata') and result.metadata:
                        if 'mx_valid' in result.metadata:
                            print(f"{'':35}   MX Valid: {result.metadata['mx_valid']}")
                        if 'checks_performed' in result.metadata:
                            print(f"{'':35}   Checks: {result.metadata['checks_performed']}")
                except Exception as e:
                    print(f"{email:<35} → Error: {e}")
                    
        except Exception as e:
            print(f"❌ Could not test MX checking: {e}")
        
        # Test 3: With disposable email detection
        print(f"\n🗑️  TEST 3: With Disposable Email Detection")
        print("-" * 50)
        
        try:
            validator_disp = EmailValidator(check_disposable=True)
            
            disposable_test_emails = [
                "user@gmail.com",           # Legitimate
                "test@10minutemail.com",    # Known disposable
                "user@temp-mail.org",       # Known disposable
                "admin@guerrillamail.com"   # Known disposable
            ]
            
            for email in disposable_test_emails:
                try:
                    result = validator_disp.validate(email)
                    print(f"{email:<35} → Valid: {result.is_valid}")
                    
                    # Show disposable-specific info
                    if hasattr(result, 'metadata') and result.metadata:
                        if 'is_disposable' in result.metadata:
                            print(f"{'':35}   Disposable: {result.metadata['is_disposable']}")
                    
                    if hasattr(result, 'errors') and result.errors:
                        print(f"{'':35}   Errors: {result.errors}")
                except Exception as e:
                    print(f"{email:<35} → Error: {e}")
                    
        except Exception as e:
            print(f"❌ Could not test disposable detection: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import or test email validator: {e}")
        return False

def show_answer():
    """Show the answer to the original question"""
    print("\n" + "=" * 60)
    print("📝 ANSWER TO YOUR QUESTION")
    print("=" * 60)
    
    print("""
🎯 QUESTION: "Does the email validator check against the email service 
   provider to see if the provided email is valid or are we currently 
   just checking formats?"

📋 ANSWER:

By DEFAULT, the PyIDVerify email validator ONLY checks FORMAT/SYNTAX.
It does NOT verify with email service providers.

However, it CAN do much more when configured:

1. 📧 FORMAT CHECKING (Default - Always ON):
   ✅ Validates email syntax according to RFC 5322
   ✅ Checks for proper @ placement, valid characters
   ✅ Verifies length limits and structure
   
2. 🌐 MX RECORD VERIFICATION (Optional):
   Use: EmailValidator(check_mx=True)
   ✅ Queries DNS to check if domain has mail servers
   ✅ Verifies the domain CAN receive emails
   ❌ Does NOT check if specific email address exists
   
3. 🗑️  DISPOSABLE EMAIL DETECTION (Optional):
   Use: EmailValidator(check_disposable=True) 
   ✅ Detects temporary/throwaway email services
   ✅ Blocks 10minutemail.com, temp-mail.org, etc.
   
4. 📊 DOMAIN REPUTATION (Optional):
   Use: EmailValidator(check_domain_reputation=True)
   ✅ Checks domain reputation scores
   ✅ Flags domains with poor sending history

🔧 TO GET MAXIMUM VALIDATION:
   validator = EmailValidator(
       check_mx=True,              # Verify domain has mail servers
       check_disposable=True,      # Block disposable emails  
       check_domain_reputation=True # Check domain reputation
   )

⚠️  IMPORTANT LIMITATIONS:
   - Does NOT verify if specific email ADDRESS exists
   - Does NOT contact email providers directly
   - Full email verification would require SMTP probing
   - SMTP probing is often blocked and considered intrusive

🎯 SUMMARY:
   Default = Format checking only
   With options = Format + DNS + Reputation + Disposable detection
   But NOT full email address existence verification
""")

def main():
    """Main function"""
    print("PyIDVerify Email Validator Analysis")
    
    # Show the direct answer first
    show_answer()
    
    # Then demonstrate with tests
    success = test_email_validator_simple()
    
    print("\n" + "=" * 60)
    print("🏁 CONCLUSION")
    print("=" * 60)
    
    if success:
        print("✅ Email validator analysis completed!")
        print("\n💡 Key Takeaway:")
        print("   By default: Only format checking")
        print("   With options: Format + DNS + Reputation checks")
        print("   But NOT full email address existence verification")
    else:
        print("❌ Some tests failed, but analysis shows capabilities")
    
    return 0

if __name__ == "__main__":
    exit(main())
