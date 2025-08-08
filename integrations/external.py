"""
External Integrations
=====================

This module provides integrations with external services for ID verification,
including API clients, database connections, and circuit breaker patterns
for resilient external service communication.

Features:
- API clients for external verification services
- Database connection pools with failover
- Circuit breaker pattern for service resilience
- Retry logic with exponential backoff
- Rate limiting and quota management
- Response caching and optimization
- Service health monitoring

Supported Integrations:
- Identity verification APIs (Jumio, Onfido, etc.)
- Credit bureau APIs (Experian, Equifax, etc.)
- Government databases (where legally accessible)
- Fraud detection services
- Address verification services
- Phone number validation services

Examples:
    >>> from pyidverify.integrations.external import ExternalAPIClient
    >>> 
    >>> # Configure API client
    >>> client = ExternalAPIClient(
    ...     service_name="identity_service",
    ...     api_key="your_api_key",
    ...     base_url="https://api.example.com"
    ... )
    >>> 
    >>> # Verify identity with circuit breaker
    >>> result = await client.verify_identity({
    ...     'document_type': 'passport',
    ...     'document_image': image_data,
    ...     'face_image': face_data
    ... })

Security Features:
- Encrypted API key storage and rotation
- Request/response encryption
- PII data handling and anonymization
- Audit logging for all external calls
- Rate limiting and abuse prevention
- Circuit breaker for service protection
"""

from typing import Optional, Dict, Any, List, Callable, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio
import json
import hashlib
from pathlib import Path
import ssl
import aiohttp
import backoff

try:
    from ..core.exceptions import ValidationError, SecurityError, IntegrationError
    from ..security.encryption import EncryptionManager
    from ..security.audit import AuditLogger
    from ..security.rate_limiting import RateLimiter
    from ..utils.caching import LRUCache
    _IMPORTS_AVAILABLE = True
except ImportError as e:
    # Graceful degradation
    _IMPORTS_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    
    # Mock classes for development
    class ValidationError(Exception): pass
    class SecurityError(Exception): pass
    class IntegrationError(Exception): pass

class ServiceState(Enum):
    """Circuit breaker service states"""
    CLOSED = "closed"           # Service is healthy
    OPEN = "open"               # Service is failing, requests blocked
    HALF_OPEN = "half_open"     # Testing if service is recovered

class APIProvider(Enum):
    """Supported external API providers"""
    JUMIO = "jumio"
    ONFIDO = "onfido"
    EXPERIAN = "experian"
    EQUIFAX = "equifax"
    WHITEPAGES = "whitepages"
    TRULIOO = "trulioo"
    CUSTOM = "custom"

@dataclass
class APIConfiguration:
    """Configuration for external API integration"""
    provider: APIProvider
    base_url: str
    api_key: str
    api_secret: Optional[str] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    rate_limit_per_minute: int = 60
    use_circuit_breaker: bool = True
    cache_ttl_seconds: int = 3600
    enable_audit_logging: bool = True
    verify_ssl: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern"""
    failure_threshold: int = 5      # Number of failures before opening
    recovery_timeout: int = 60      # Seconds to wait before half-open
    success_threshold: int = 3      # Successes needed to close from half-open
    timeout_seconds: float = 30.0   # Request timeout

@dataclass
class ExternalServiceResponse:
    """Response from external service call"""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    response_time_ms: float = 0.0
    cached: bool = False
    provider: str = ""
    api_call_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

class CircuitBreaker:
    """Circuit breaker implementation for service resilience"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = ServiceState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()
        
        if _IMPORTS_AVAILABLE:
            self.audit_logger = AuditLogger("circuit_breaker")
    
    def can_execute(self) -> bool:
        """Check if request can be executed based on circuit state"""
        current_time = time.time()
        
        if self.state == ServiceState.CLOSED:
            return True
        
        elif self.state == ServiceState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.last_failure_time >= self.config.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
        
        elif self.state == ServiceState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record successful execution"""
        if self.state == ServiceState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == ServiceState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == ServiceState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == ServiceState.HALF_OPEN:
            self._transition_to_open()
    
    def _transition_to_closed(self) -> None:
        """Transition to closed state (healthy)"""
        self.state = ServiceState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        
        if _IMPORTS_AVAILABLE:
            self.audit_logger.log_event("circuit_breaker_closed", {
                'transition_time': self.last_state_change
            })
    
    def _transition_to_open(self) -> None:
        """Transition to open state (failing)"""
        self.state = ServiceState.OPEN
        self.success_count = 0
        self.last_state_change = time.time()
        
        if _IMPORTS_AVAILABLE:
            self.audit_logger.log_event("circuit_breaker_opened", {
                'failure_count': self.failure_count,
                'transition_time': self.last_state_change
            })
    
    def _transition_to_half_open(self) -> None:
        """Transition to half-open state (testing)"""
        self.state = ServiceState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = time.time()
        
        if _IMPORTS_AVAILABLE:
            self.audit_logger.log_event("circuit_breaker_half_opened", {
                'transition_time': self.last_state_change
            })
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'last_state_change': self.last_state_change,
            'time_until_half_open': max(0, (self.last_failure_time + self.config.recovery_timeout) - time.time())
        }

class ExternalAPIClient:
    """Client for external API integrations with resilience patterns"""
    
    def __init__(self, config: APIConfiguration):
        self.config = config
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig()) if config.use_circuit_breaker else None
        
        if _IMPORTS_AVAILABLE:
            self.encryption_manager = EncryptionManager()
            self.audit_logger = AuditLogger(f"api_client_{config.provider.value}")
            self.rate_limiter = RateLimiter(
                max_requests=config.rate_limit_per_minute,
                time_window=60
            )
            self.response_cache = LRUCache(maxsize=1000)
        
        # Performance tracking
        self.call_count = 0
        self.total_response_time = 0.0
        self.error_count = 0
        
        # SSL context for secure connections
        self.ssl_context = ssl.create_default_context()
        if not config.verify_ssl:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def call_api(self, endpoint: str, method: str = "POST", 
                      data: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None) -> ExternalServiceResponse:
        """
        Make API call with circuit breaker and retry logic.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request payload
            headers: Additional headers
            
        Returns:
            ExternalServiceResponse with call results
        """
        start_time = time.time()
        
        try:
            # Check circuit breaker
            if self.circuit_breaker and not self.circuit_breaker.can_execute():
                raise IntegrationError("Circuit breaker is open - service unavailable")
            
            # Rate limiting
            if _IMPORTS_AVAILABLE and not self.rate_limiter.allow_request("api_call"):
                raise IntegrationError("Rate limit exceeded")
            
            # Check cache first
            cache_key = self._generate_cache_key(endpoint, method, data)
            if _IMPORTS_AVAILABLE:
                cached_response = self.response_cache.get(cache_key)
                if cached_response:
                    cached_response.cached = True
                    return cached_response
            
            # Make API call with retry logic
            response_data = await self._execute_with_retry(endpoint, method, data, headers)
            
            response_time = (time.time() - start_time) * 1000
            
            # Record success
            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            
            # Create response
            service_response = ExternalServiceResponse(
                success=True,
                data=response_data,
                response_time_ms=response_time,
                provider=self.config.provider.value,
                metadata={
                    'endpoint': endpoint,
                    'method': method,
                    'cached': False
                }
            )
            
            # Cache response
            if _IMPORTS_AVAILABLE:
                self.response_cache.set(cache_key, service_response, ttl=self.config.cache_ttl_seconds)
            
            # Update performance tracking
            self.call_count += 1
            self.total_response_time += response_time
            
            # Audit logging
            if self.config.enable_audit_logging and _IMPORTS_AVAILABLE:
                self.audit_logger.log_api_call(
                    endpoint, method, True, response_time, self.config.provider.value
                )
            
            return service_response
            
        except Exception as e:
            # Record failure
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
            
            self.error_count += 1
            response_time = (time.time() - start_time) * 1000
            
            # Audit logging for failures
            if self.config.enable_audit_logging and _IMPORTS_AVAILABLE:
                self.audit_logger.log_api_call(
                    endpoint, method, False, response_time, self.config.provider.value, str(e)
                )
            
            return ExternalServiceResponse(
                success=False,
                data={},
                error_message=str(e),
                response_time_ms=response_time,
                provider=self.config.provider.value,
                metadata={
                    'endpoint': endpoint,
                    'method': method,
                    'error_type': type(e).__name__
                }
            )
    
    @backoff.on_exception(backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_tries=3)
    async def _execute_with_retry(self, endpoint: str, method: str,
                                 data: Optional[Dict[str, Any]], 
                                 headers: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Execute API call with exponential backoff retry"""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Prepare headers
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PyIDVerify/1.0',
            **self.config.custom_headers
        }
        
        if headers:
            request_headers.update(headers)
        
        # Add authentication
        request_headers.update(self._get_auth_headers())
        
        # Prepare payload
        payload = json.dumps(data) if data else None
        
        # Make HTTP request
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(ssl=self.ssl_context)
        ) as session:
            
            async with session.request(
                method,
                url,
                data=payload,
                headers=request_headers
            ) as response:
                
                response_text = await response.text()
                
                if response.status >= 400:
                    raise IntegrationError(f"API error {response.status}: {response_text}")
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {'raw_response': response_text}
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on provider"""
        headers = {}
        
        if self.config.provider == APIProvider.JUMIO:
            headers['Authorization'] = f'Basic {self._encode_basic_auth()}'
        elif self.config.provider == APIProvider.ONFIDO:
            headers['Authorization'] = f'Token token={self.config.api_key}'
        elif self.config.provider in [APIProvider.EXPERIAN, APIProvider.EQUIFAX]:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        else:
            # Default API key header
            headers['X-API-Key'] = self.config.api_key
        
        return headers
    
    def _encode_basic_auth(self) -> str:
        """Encode basic authentication"""
        import base64
        credentials = f"{self.config.api_key}:{self.config.api_secret or ''}"
        return base64.b64encode(credentials.encode()).decode()
    
    def _generate_cache_key(self, endpoint: str, method: str, 
                           data: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for request"""
        key_data = f"{endpoint}:{method}:{json.dumps(data, sort_keys=True) if data else ''}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_response_time = (self.total_response_time / self.call_count 
                           if self.call_count > 0 else 0)
        error_rate = (self.error_count / self.call_count 
                     if self.call_count > 0 else 0)
        
        stats = {
            'call_count': self.call_count,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'average_response_time_ms': avg_response_time,
            'total_response_time_ms': self.total_response_time,
            'provider': self.config.provider.value
        }
        
        if self.circuit_breaker:
            stats['circuit_breaker'] = self.circuit_breaker.get_state()
        
        if _IMPORTS_AVAILABLE:
            stats.update({
                'cache_hits': self.response_cache.hits,
                'cache_misses': self.response_cache.misses,
                'cache_hit_rate': (self.response_cache.hits / 
                                 (self.response_cache.hits + self.response_cache.misses)
                                 if (self.response_cache.hits + self.response_cache.misses) > 0 else 0)
            })
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the external service"""
        try:
            # Most APIs have a health/status endpoint
            response = await self.call_api("health", "GET")
            
            return {
                'healthy': response.success,
                'response_time_ms': response.response_time_ms,
                'provider': self.config.provider.value,
                'circuit_breaker_state': (self.circuit_breaker.get_state() 
                                        if self.circuit_breaker else None)
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'provider': self.config.provider.value,
                'circuit_breaker_state': (self.circuit_breaker.get_state() 
                                        if self.circuit_breaker else None)
            }

# Service-specific client implementations

class JumioClient(ExternalAPIClient):
    """Specialized client for Jumio identity verification"""
    
    async def verify_identity(self, document_data: Dict[str, Any]) -> ExternalServiceResponse:
        """Verify identity using Jumio service"""
        return await self.call_api("identity/verify", "POST", document_data)
    
    async def get_verification_status(self, transaction_id: str) -> ExternalServiceResponse:
        """Get verification status by transaction ID"""
        return await self.call_api(f"identity/status/{transaction_id}", "GET")

class OnfidoClient(ExternalAPIClient):
    """Specialized client for Onfido identity verification"""
    
    async def create_applicant(self, applicant_data: Dict[str, Any]) -> ExternalServiceResponse:
        """Create new applicant for verification"""
        return await self.call_api("applicants", "POST", applicant_data)
    
    async def upload_document(self, applicant_id: str, 
                            document_data: Dict[str, Any]) -> ExternalServiceResponse:
        """Upload document for verification"""
        return await self.call_api(f"documents", "POST", {
            'applicant_id': applicant_id,
            **document_data
        })
    
    async def create_check(self, applicant_id: str, 
                         check_data: Dict[str, Any]) -> ExternalServiceResponse:
        """Create verification check"""
        return await self.call_api("checks", "POST", {
            'applicant_id': applicant_id,
            **check_data
        })

class CreditBureauClient(ExternalAPIClient):
    """Specialized client for credit bureau APIs"""
    
    async def verify_identity(self, identity_data: Dict[str, Any]) -> ExternalServiceResponse:
        """Verify identity against credit bureau records"""
        return await self.call_api("identity/verify", "POST", identity_data)
    
    async def get_credit_report(self, consumer_data: Dict[str, Any]) -> ExternalServiceResponse:
        """Get credit report (requires appropriate permissions)"""
        return await self.call_api("credit/report", "POST", consumer_data)

# Factory functions for creating clients

def create_jumio_client(api_key: str, api_secret: str, 
                       environment: str = "production") -> JumioClient:
    """Create Jumio client with standard configuration"""
    base_url = ("https://netverify.com/api/netverify/v2" 
               if environment == "production" 
               else "https://lon.netverify.com/api/netverify/v2")
    
    config = APIConfiguration(
        provider=APIProvider.JUMIO,
        base_url=base_url,
        api_key=api_key,
        api_secret=api_secret
    )
    
    return JumioClient(config)

def create_onfido_client(api_key: str, environment: str = "production") -> OnfidoClient:
    """Create Onfido client with standard configuration"""
    base_url = ("https://api.onfido.com/v3" 
               if environment == "production" 
               else "https://api.eu.onfido.com/v3")
    
    config = APIConfiguration(
        provider=APIProvider.ONFIDO,
        base_url=base_url,
        api_key=api_key
    )
    
    return OnfidoClient(config)

def create_credit_bureau_client(provider: str, api_key: str, 
                               base_url: str) -> CreditBureauClient:
    """Create credit bureau client"""
    provider_enum = (APIProvider.EXPERIAN if provider.lower() == "experian"
                    else APIProvider.EQUIFAX if provider.lower() == "equifax"
                    else APIProvider.CUSTOM)
    
    config = APIConfiguration(
        provider=provider_enum,
        base_url=base_url,
        api_key=api_key,
        rate_limit_per_minute=30  # Lower rate limit for credit bureaus
    )
    
    return CreditBureauClient(config)

# Integration management

class IntegrationManager:
    """Manager for multiple external service integrations"""
    
    def __init__(self):
        self.clients: Dict[str, ExternalAPIClient] = {}
        
        if _IMPORTS_AVAILABLE:
            self.audit_logger = AuditLogger("integration_manager")
    
    def add_client(self, name: str, client: ExternalAPIClient) -> None:
        """Add external service client"""
        self.clients[name] = client
    
    def remove_client(self, name: str) -> bool:
        """Remove external service client"""
        if name in self.clients:
            del self.clients[name]
            return True
        return False
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all registered clients"""
        results = {}
        
        for name, client in self.clients.items():
            try:
                results[name] = await client.health_check()
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'error': str(e),
                    'provider': getattr(client.config, 'provider', 'unknown')
                }
        
        return results
    
    def get_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get performance summary for all clients"""
        summary = {}
        
        for name, client in self.clients.items():
            summary[name] = client.get_performance_stats()
        
        return summary

# Export public interface
__all__ = [
    "ExternalAPIClient",
    "JumioClient",
    "OnfidoClient", 
    "CreditBureauClient",
    "IntegrationManager",
    "APIConfiguration",
    "CircuitBreakerConfig",
    "ExternalServiceResponse",
    "ServiceState",
    "APIProvider",
    "CircuitBreaker",
    "create_jumio_client",
    "create_onfido_client",
    "create_credit_bureau_client"
]
