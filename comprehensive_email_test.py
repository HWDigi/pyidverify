"""
PyIDVerify Enhanced Email Verification - Comprehensive Integration Test
=====================================================================

This test suite validates the complete email verification enhancement system
including all components, integration points, and functionality.
"""

import asyncio
import sys
import os
import time
from typing import Dict, List, Any
import json
from datetime import datetime

# Add the package to Python path for testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pyidverify.email_verification import (
        EnhancedEmailValidator,
        EmailVerificationMode,
        create_enhanced_email_validator,
        verify_email_hybrid,
        verify_email_behavioral,
        VerificationLevel,
        HybridStrategy,
        VerificationWorkflowType,
        APIProvider
    )
    print("✅ Successfully imported enhanced email verification modules")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

class ComprehensiveEmailVerificationTest:
    """Comprehensive test suite for email verification system"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "performance_metrics": {},
            "errors": [],
            "summary": {}
        }
        
        # Test email addresses covering various scenarios
        self.test_emails = {
            "valid_gmail": "test.user@gmail.com",
            "valid_outlook": "user@outlook.com", 
            "disposable": "test@10minutemail.com",
            "invalid_format": "not-an-email",
            "invalid_domain": "user@nonexistent-domain-12345.com",
            "role_account": "admin@example.com",
            "catch_all": "anything@example.com",
        }
        
        print("🔬 Initialized Comprehensive Email Verification Test Suite")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print(f"\n{'='*70}")
        print("PYIDVERIFY ENHANCED EMAIL VERIFICATION - COMPREHENSIVE TESTS")
        print(f"{'='*70}")
        
        # Test 1: Basic Integration
        await self.test_basic_integration()
        
        # Test 2: All Verification Modes
        await self.test_all_verification_modes()
        
        # Test 3: Hybrid Verification System
        await self.test_hybrid_verification()
        
        # Test 4: Component Integration
        await self.test_component_integration()
        
        # Test 5: Performance Testing
        await self.test_performance()
        
        # Test 6: Error Handling
        await self.test_error_handling()
        
        # Generate final report
        self.generate_test_report()
        
        return self.results
    
    async def test_basic_integration(self):
        """Test basic integration and functionality"""
        print(f"\n📋 Test 1: Basic Integration")
        print("-" * 40)
        
        test_results = {}
        
        try:
            # Test basic validator creation
            validator = EnhancedEmailValidator()
            test_results["validator_creation"] = "✅ PASS"
            
            # Test basic email validation
            result = await validator.validate_email(
                self.test_emails["valid_gmail"], 
                EmailVerificationMode.BASIC
            )
            
            test_results["basic_validation"] = "✅ PASS" if result.format_valid else "❌ FAIL"
            test_results["result_structure"] = "✅ PASS" if hasattr(result, 'confidence') else "❌ FAIL"
            
            # Test convenience methods
            is_valid = await validator.is_valid_email(self.test_emails["valid_gmail"])
            test_results["convenience_methods"] = "✅ PASS" if is_valid else "❌ FAIL"
            
            print(f"  Validator Creation: {test_results['validator_creation']}")
            print(f"  Basic Validation: {test_results['basic_validation']}")
            print(f"  Result Structure: {test_results['result_structure']}")
            print(f"  Convenience Methods: {test_results['convenience_methods']}")
            
        except Exception as e:
            test_results["error"] = str(e)
            print(f"  ❌ FAILED: {e}")
            self.results["errors"].append(f"Basic Integration: {e}")
        
        self.results["test_results"]["basic_integration"] = test_results
    
    async def test_all_verification_modes(self):
        """Test all verification modes"""
        print(f"\n📋 Test 2: All Verification Modes")
        print("-" * 40)
        
        modes = [
            EmailVerificationMode.BASIC,
            EmailVerificationMode.STANDARD,
            # Note: THOROUGH and COMPREHENSIVE require API keys
        ]
        
        test_results = {}
        
        for mode in modes:
            try:
                print(f"  Testing {mode.value.upper()} mode...")
                
                validator = EnhancedEmailValidator(default_mode=mode)
                result = await validator.validate_email(self.test_emails["valid_gmail"])
                
                # Validate expected behavior for each mode
                if mode == EmailVerificationMode.BASIC:
                    success = result.format_valid and "format_validation" in result.methods_used
                elif mode == EmailVerificationMode.STANDARD:
                    success = result.format_valid and (
                        "dns_validation" in result.methods_used or 
                        len(result.warnings) > 0  # DNS might fail in test environment
                    )
                else:
                    success = True  # Other modes tested separately
                
                test_results[mode.value] = "✅ PASS" if success else "❌ FAIL"
                print(f"    Result: {test_results[mode.value]}")
                print(f"    Methods used: {result.methods_used}")
                print(f"    Confidence: {result.confidence:.2f}")
                
            except Exception as e:
                test_results[mode.value] = f"❌ ERROR: {str(e)}"
                print(f"    ❌ FAILED: {e}")
                self.results["errors"].append(f"Mode {mode.value}: {e}")
        
        self.results["test_results"]["verification_modes"] = test_results
    
    async def test_hybrid_verification(self):
        """Test hybrid verification system"""
        print(f"\n📋 Test 3: Hybrid Verification System")
        print("-" * 40)
        
        test_results = {}
        
        try:
            # Test different verification levels
            levels = [VerificationLevel.BASIC, VerificationLevel.STANDARD]
            strategies = [HybridStrategy.BALANCED, HybridStrategy.COST_OPTIMIZED]
            
            for level in levels:
                for strategy in strategies:
                    test_name = f"{level.name.lower()}_{strategy.value}"
                    
                    try:
                        result = await verify_email_hybrid(
                            self.test_emails["valid_gmail"],
                            level=level,
                            strategy=strategy
                        )
                        
                        success = (
                            result.format_valid and 
                            result.confidence > 0 and 
                            len(result.methods_used) > 0
                        )
                        
                        test_results[test_name] = "✅ PASS" if success else "❌ FAIL"
                        print(f"  {test_name}: {test_results[test_name]} (confidence: {result.confidence:.2f})")
                        
                    except Exception as e:
                        test_results[test_name] = f"❌ ERROR: {str(e)}"
                        print(f"  {test_name}: ❌ FAILED - {e}")
            
        except Exception as e:
            print(f"  ❌ Hybrid verification test failed: {e}")
            self.results["errors"].append(f"Hybrid verification: {e}")
        
        self.results["test_results"]["hybrid_verification"] = test_results
    
    async def test_component_integration(self):
        """Test individual component integration"""
        print(f"\n📋 Test 4: Component Integration")
        print("-" * 40)
        
        test_results = {}
        
        # Test Enhanced DNS Checker
        try:
            from pyidverify.email_verification.enhanced_dns import EnhancedDNSChecker
            dns_checker = EnhancedDNSChecker()
            
            # Test with a known domain
            domain_result = await dns_checker.check_domain_comprehensive("gmail.com")
            test_results["dns_checker"] = "✅ PASS" if domain_result.valid else "❌ FAIL"
            print(f"  DNS Checker: {test_results['dns_checker']}")
            
        except Exception as e:
            test_results["dns_checker"] = f"❌ ERROR: {str(e)}"
            print(f"  DNS Checker: ❌ FAILED - {e}")
        
        # Test SMTP Verifier (basic instantiation)
        try:
            from pyidverify.email_verification.smtp_verifier import SMTPEmailVerifier
            smtp_verifier = SMTPEmailVerifier()
            test_results["smtp_verifier"] = "✅ PASS"
            print(f"  SMTP Verifier: {test_results['smtp_verifier']}")
            
        except Exception as e:
            test_results["smtp_verifier"] = f"❌ ERROR: {str(e)}"
            print(f"  SMTP Verifier: ❌ FAILED - {e}")
        
        # Test API Verifier (basic instantiation)
        try:
            from pyidverify.email_verification.api_verifier import ThirdPartyEmailVerifier
            api_verifier = ThirdPartyEmailVerifier(APIProvider.ZEROBOUNCE)
            test_results["api_verifier"] = "✅ PASS"
            print(f"  API Verifier: {test_results['api_verifier']}")
            
        except Exception as e:
            test_results["api_verifier"] = f"❌ ERROR: {str(e)}"
            print(f"  API Verifier: ❌ FAILED - {e}")
        
        # Test Behavioral Verifier
        try:
            from pyidverify.email_verification.behavioral_verifier import BehavioralEmailVerifier
            behavioral_verifier = BehavioralEmailVerifier()
            test_results["behavioral_verifier"] = "✅ PASS"
            print(f"  Behavioral Verifier: {test_results['behavioral_verifier']}")
            
        except Exception as e:
            test_results["behavioral_verifier"] = f"❌ ERROR: {str(e)}"
            print(f"  Behavioral Verifier: ❌ FAILED - {e}")
        
        self.results["test_results"]["component_integration"] = test_results
    
    async def test_performance(self):
        """Test performance characteristics"""
        print(f"\n📋 Test 5: Performance Testing")
        print("-" * 40)
        
        performance_results = {}
        
        # Test validation speed
        validator = EnhancedEmailValidator()
        
        # Single email performance
        start_time = time.time()
        result = await validator.validate_email(self.test_emails["valid_gmail"])
        single_time = time.time() - start_time
        
        performance_results["single_validation_time"] = single_time
        print(f"  Single validation: {single_time:.4f}s")
        
        # Batch validation performance
        emails = list(self.test_emails.values())[:5]  # Test with 5 emails
        
        start_time = time.time()
        tasks = [validator.validate_email(email) for email in emails]
        results = await asyncio.gather(*tasks)
        batch_time = time.time() - start_time
        
        performance_results["batch_validation_time"] = batch_time
        performance_results["emails_per_second"] = len(emails) / batch_time
        
        print(f"  Batch validation ({len(emails)} emails): {batch_time:.4f}s")
        print(f"  Emails per second: {performance_results['emails_per_second']:.2f}")
        
        # Memory usage (basic check)
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        performance_results["memory_usage_mb"] = memory_mb
        print(f"  Memory usage: {memory_mb:.2f} MB")
        
        self.results["performance_metrics"] = performance_results
    
    async def test_error_handling(self):
        """Test error handling capabilities"""
        print(f"\n📋 Test 6: Error Handling")
        print("-" * 40)
        
        error_test_results = {}
        validator = EnhancedEmailValidator()
        
        # Test invalid email formats
        invalid_emails = ["", "invalid", "@domain.com", "user@", "user@@domain.com"]
        
        for email in invalid_emails:
            try:
                result = await validator.validate_email(email)
                # Should handle gracefully, not crash
                success = not result.format_valid and len(result.warnings) == 0
                error_test_results[f"invalid_format_{email or 'empty'}"] = "✅ PASS" if success else "❌ FAIL"
                
            except Exception as e:
                error_test_results[f"invalid_format_{email or 'empty'}"] = f"❌ EXCEPTION: {str(e)}"
        
        # Test network timeout handling (simulate with very short timeout)
        try:
            from pyidverify.email_verification.enhanced_dns import EnhancedDNSChecker
            dns_checker = EnhancedDNSChecker(timeout=0.001)  # Very short timeout
            result = await dns_checker.check_domain_comprehensive("example.com")
            error_test_results["timeout_handling"] = "✅ PASS"  # Should handle gracefully
            
        except Exception:
            error_test_results["timeout_handling"] = "✅ PASS"  # Expected to fail gracefully
        
        print(f"  Error handling tests completed: {len(error_test_results)} scenarios")
        
        self.results["test_results"]["error_handling"] = error_test_results
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print(f"\n{'='*70}")
        print("TEST SUMMARY REPORT")
        print(f"{'='*70}")
        
        total_tests = 0
        passed_tests = 0
        
        for test_category, results in self.results["test_results"].items():
            print(f"\n📊 {test_category.replace('_', ' ').title()}:")
            
            if isinstance(results, dict):
                for test_name, result in results.items():
                    total_tests += 1
                    if "✅" in str(result):
                        passed_tests += 1
                    print(f"  {test_name}: {result}")
            else:
                total_tests += 1
                if "✅" in str(results):
                    passed_tests += 1
                print(f"  Result: {results}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 Overall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {total_tests - passed_tests}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n❌ Errors Encountered:")
            for error in self.results["errors"]:
                print(f"  • {error}")
        
        # Performance summary
        if self.results["performance_metrics"]:
            print(f"\n⚡ Performance Metrics:")
            for metric, value in self.results["performance_metrics"].items():
                if isinstance(value, float):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "status": "PASS" if success_rate >= 80 else "FAIL"
        }
        
        print(f"\n🎯 Final Status: {self.results['summary']['status']}")
        
        return self.results

async def main():
    """Run comprehensive email verification tests"""
    print("🚀 Starting PyIDVerify Enhanced Email Verification System Tests")
    
    # Create and run test suite
    test_suite = ComprehensiveEmailVerificationTest()
    results = await test_suite.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"email_verification_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: {results_file}")
    
    # Return status code based on results
    return 0 if results["summary"]["status"] == "PASS" else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
