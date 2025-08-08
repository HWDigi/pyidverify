#!/usr/bin/env python3
"""
SSN Validator Test Script
========================

This script tests the SSN validator to identify any issues after workspace cleanup.
"""

import sys
import traceback
from pathlib import Path

def test_ssn_validator():
    """Test SSN validator functionality"""
    print("=" * 60)
    print("SSN VALIDATOR TEST SCRIPT")
    print("=" * 60)
    
    try:
        print("Step 1: Testing SSN validator import...")
        from pyidverify.validators.government.ssn import SSNValidator
        print("✅ SSN validator imported successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import SSN validator: {e}")
        print("\nTrying alternative import path...")
        try:
            from validators.government.ssn import SSNValidator
            print("✅ SSN validator imported via alternative path")
        except ImportError as e2:
            print(f"❌ Alternative import also failed: {e2}")
            return False
    
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        return False
    
    try:
        print("\nStep 2: Creating SSN validator instance...")
        validator = SSNValidator()
        print("✅ SSN validator instance created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create SSN validator instance: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        return False
    
    try:
        print("\nStep 3: Testing SSN validation...")
        test_ssns = [
            "123-45-6789",
            "000-00-0000",  # Invalid
            "123456789",    # No dashes
            "invalid"       # Invalid format
        ]
        
        for ssn in test_ssns:
            print(f"\nTesting SSN: {ssn}")
            try:
                result = validator.validate(ssn)
                print(f"  ✅ Validation completed")
                print(f"  Valid: {result.is_valid}")
                print(f"  Result type: {type(result)}")
                
                if hasattr(result, 'errors'):
                    print(f"  Errors: {result.errors}")
                if hasattr(result, 'metadata'):
                    print(f"  Metadata keys: {list(result.metadata.keys()) if result.metadata else 'None'}")
                if hasattr(result, 'confidence'):
                    print(f"  Confidence: {result.confidence}")
                    
            except Exception as e:
                print(f"  ❌ Validation failed for {ssn}: {e}")
                print(f"  Traceback: {traceback.format_exc()}")
        
        print("\n✅ SSN validator test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ SSN validation test failed: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        return False

def test_other_validators():
    """Test other core validators"""
    print("\n" + "=" * 60)
    print("OTHER VALIDATORS TEST")
    print("=" * 60)
    
    validators_to_test = [
        ("Email", "pyidverify.validators.personal.email", "EmailValidator", "test@example.com"),
        ("Credit Card", "pyidverify.validators.financial.credit_card", "CreditCardValidator", "4111111111111111")
    ]
    
    working_validators = []
    
    for name, module_path, class_name, test_value in validators_to_test:
        try:
            print(f"\nTesting {name} validator...")
            exec(f"from {module_path} import {class_name}")
            validator = eval(f"{class_name}()")
            result = validator.validate(test_value)
            print(f"✅ {name} validator works: Valid={result.is_valid}")
            working_validators.append(name)
            
        except Exception as e:
            print(f"❌ {name} validator failed: {e}")
    
    print(f"\nWorking validators: {working_validators}")
    return working_validators

def main():
    """Main test function"""
    print("PyIDVerify SSN Validator Test")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Test SSN validator specifically
    ssn_success = test_ssn_validator()
    
    # Test other validators
    working_validators = test_other_validators()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if ssn_success:
        print("✅ SSN validator is working correctly")
    else:
        print("❌ SSN validator has issues")
    
    print(f"Working validators: {len(working_validators)}")
    print(f"Validator list: {working_validators}")
    
    if ssn_success and len(working_validators) >= 2:
        print("\n🎉 PACKAGE IS FUNCTIONAL AFTER CLEANUP!")
        return 0
    else:
        print("\n⚠️  SOME VALIDATORS NEED ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
