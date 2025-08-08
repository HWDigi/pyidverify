"""
Integrations Package
===================

This package provides integration capabilities for external services and
data storage systems, including:

1. **External API Integrations**: Identity verification services, credit bureaus, fraud detection
2. **Database Integrations**: Multi-database support with connection pooling and failover
3. **Caching Systems**: Redis integration for high-performance caching
4. **Message Queues**: Integration with message queue systems for async processing

Features:
- Circuit breaker pattern for service resilience
- Connection pooling and automatic failover
- Retry logic with exponential backoff
- Rate limiting and quota management
- Response caching and optimization
- Service health monitoring and alerting
- Comprehensive audit logging

Supported Services:
- Identity verification APIs (Jumio, Onfido, Trulioo)
- Credit bureau APIs (Experian, Equifax)
- Government databases (where legally accessible)
- Fraud detection services
- Address verification services
- Phone number validation services

Database Support:
- PostgreSQL (recommended for production)
- MySQL/MariaDB
- SQLite (development/testing)
- MongoDB (document storage)
- Redis (caching and sessions)

Examples:
    >>> from pyidverify.integrations import ExternalAPIClient, DatabaseManager
    >>> 
    >>> # External API integration
    >>> client = ExternalAPIClient(config)
    >>> result = await client.verify_identity(data)
    >>> 
    >>> # Database integration
    >>> db = DatabaseManager(db_config)
    >>> await db.store_validation_result(result)

Security Features:
- Encrypted API credentials and connection strings
- Request/response encryption for sensitive data
- PII data handling and anonymization
- Comprehensive audit trails
- Rate limiting and abuse prevention
- Circuit breakers for service protection
"""

from typing import Dict, Any, List, Optional
import time

# Import main integration classes with graceful degradation
try:
    from .external import (
        ExternalAPIClient,
        JumioClient,
        OnfidoClient,
        CreditBureauClient,
        IntegrationManager,
        APIConfiguration,
        CircuitBreakerConfig,
        ExternalServiceResponse,
        ServiceState,
        APIProvider,
        CircuitBreaker,
        create_jumio_client,
        create_onfido_client,
        create_credit_bureau_client
    )
    _EXTERNAL_INTEGRATIONS_AVAILABLE = True
except ImportError:
    _EXTERNAL_INTEGRATIONS_AVAILABLE = False

try:
    from .database import (
        DatabaseManager,
        DatabaseConnection,
        DatabaseConfig,
        ValidationRecord,
        AuditRecord,
        DatabaseType,
        ConnectionState,
        create_postgresql_manager,
        create_mysql_manager,
        create_sqlite_manager,
        create_mongodb_manager
    )
    _DATABASE_INTEGRATIONS_AVAILABLE = True
except ImportError:
    _DATABASE_INTEGRATIONS_AVAILABLE = False

def get_available_integrations() -> Dict[str, Dict[str, Any]]:
    """Get information about available integrations"""
    integrations = {}
    
    if _EXTERNAL_INTEGRATIONS_AVAILABLE:
        integrations['external_apis'] = {
            'available': True,
            'providers': [
                'jumio',
                'onfido', 
                'experian',
                'equifax',
                'trulioo',
                'custom'
            ],
            'features': [
                'circuit_breaker',
                'retry_logic',
                'rate_limiting',
                'response_caching',
                'health_monitoring',
                'audit_logging'
            ]
        }
    else:
        integrations['external_apis'] = {
            'available': False,
            'reason': 'External API dependencies not installed'
        }
    
    if _DATABASE_INTEGRATIONS_AVAILABLE:
        integrations['databases'] = {
            'available': True,
            'supported_types': [
                'postgresql',
                'mysql',
                'sqlite',
                'mongodb',
                'redis'
            ],
            'features': [
                'connection_pooling',
                'automatic_failover',
                'query_caching',
                'schema_management',
                'data_encryption',
                'audit_trails'
            ]
        }
    else:
        integrations['databases'] = {
            'available': False,
            'reason': 'Database dependencies not installed'
        }
    
    return integrations

def create_integration_client(provider: str, config: Dict[str, Any]) -> Optional[Any]:
    """
    Factory function to create integration client.
    
    Args:
        provider: Provider name (jumio, onfido, etc.)
        config: Configuration dictionary
        
    Returns:
        Integration client instance or None if not available
    """
    if not _EXTERNAL_INTEGRATIONS_AVAILABLE:
        return None
    
    provider_lower = provider.lower()
    
    if provider_lower == 'jumio':
        return create_jumio_client(
            api_key=config['api_key'],
            api_secret=config['api_secret'],
            environment=config.get('environment', 'production')
        )
    elif provider_lower == 'onfido':
        return create_onfido_client(
            api_key=config['api_key'],
            environment=config.get('environment', 'production')
        )
    elif provider_lower in ['experian', 'equifax']:
        return create_credit_bureau_client(
            provider=provider_lower,
            api_key=config['api_key'],
            base_url=config['base_url']
        )
    
    return None

def create_database_manager(database_type: str, connection_config: Dict[str, Any]) -> Optional[Any]:
    """
    Factory function to create database manager.
    
    Args:
        database_type: Type of database (postgresql, mysql, etc.)
        connection_config: Connection configuration
        
    Returns:
        Database manager instance or None if not available
    """
    if not _DATABASE_INTEGRATIONS_AVAILABLE:
        return None
    
    db_type_lower = database_type.lower()
    
    if db_type_lower == 'postgresql':
        return create_postgresql_manager(
            connection_string=connection_config['connection_string'],
            **connection_config.get('options', {})
        )
    elif db_type_lower == 'mysql':
        return create_mysql_manager(
            connection_string=connection_config['connection_string'],
            **connection_config.get('options', {})
        )
    elif db_type_lower == 'sqlite':
        return create_sqlite_manager(
            db_path=connection_config['db_path'],
            **connection_config.get('options', {})
        )
    elif db_type_lower == 'mongodb':
        return create_mongodb_manager(
            connection_string=connection_config['connection_string'],
            **connection_config.get('options', {})
        )
    
    return None

async def health_check_all_integrations(
    api_clients: Optional[Dict[str, Any]] = None,
    db_managers: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Perform health check on all registered integrations.
    
    Args:
        api_clients: Dictionary of API clients to check
        db_managers: Dictionary of database managers to check
        
    Returns:
        Health check results for all integrations
    """
    results = {}
    
    # Check API clients
    if api_clients:
        for name, client in api_clients.items():
            try:
                if hasattr(client, 'health_check'):
                    results[f"api_{name}"] = await client.health_check()
                else:
                    results[f"api_{name}"] = {
                        'healthy': False,
                        'error': 'Health check not supported'
                    }
            except Exception as e:
                results[f"api_{name}"] = {
                    'healthy': False,
                    'error': str(e)
                }
    
    # Check database managers
    if db_managers:
        for name, db in db_managers.items():
            try:
                if hasattr(db, 'connection') and hasattr(db.connection, 'health_check'):
                    results[f"db_{name}"] = await db.connection.health_check()
                else:
                    results[f"db_{name}"] = {
                        'healthy': False,
                        'error': 'Health check not supported'
                    }
            except Exception as e:
                results[f"db_{name}"] = {
                    'healthy': False,
                    'error': str(e)
                }
    
    return results

def get_recommended_configuration(use_case: str) -> Dict[str, Any]:
    """
    Get recommended configuration for common use cases.
    
    Args:
        use_case: Use case type (basic, enterprise, high_volume, etc.)
        
    Returns:
        Recommended configuration dictionary
    """
    configurations = {
        'basic': {
            'database': {
                'type': 'sqlite',
                'config': {
                    'db_path': './pyidverify.db',
                    'options': {
                        'pool_size': 5,
                        'enable_query_cache': True,
                        'cache_size': 100
                    }
                }
            },
            'external_apis': {
                'rate_limit_per_minute': 60,
                'timeout_seconds': 30.0,
                'max_retries': 3,
                'enable_circuit_breaker': True
            }
        },
        'enterprise': {
            'database': {
                'type': 'postgresql',
                'config': {
                    'connection_string': 'postgresql://user:pass@localhost/pyidverify',
                    'options': {
                        'pool_size': 20,
                        'max_overflow': 10,
                        'enable_ssl': True,
                        'enable_encryption': True,
                        'enable_query_cache': True,
                        'cache_size': 1000,
                        'backup_interval_hours': 6
                    }
                }
            },
            'external_apis': {
                'rate_limit_per_minute': 300,
                'timeout_seconds': 45.0,
                'max_retries': 5,
                'enable_circuit_breaker': True,
                'cache_ttl_seconds': 7200
            }
        },
        'high_volume': {
            'database': {
                'type': 'postgresql',
                'config': {
                    'connection_string': 'postgresql://user:pass@localhost/pyidverify',
                    'options': {
                        'pool_size': 50,
                        'max_overflow': 20,
                        'enable_ssl': True,
                        'enable_encryption': True,
                        'enable_query_cache': True,
                        'cache_size': 5000,
                        'backup_interval_hours': 2
                    }
                }
            },
            'external_apis': {
                'rate_limit_per_minute': 1000,
                'timeout_seconds': 60.0,
                'max_retries': 7,
                'enable_circuit_breaker': True,
                'cache_ttl_seconds': 14400,
                'failure_threshold': 10,
                'recovery_timeout': 30
            }
        }
    }
    
    return configurations.get(use_case, configurations['basic'])

# Integration monitoring and metrics

class IntegrationMonitor:
    """Monitor integration health and performance"""
    
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'successful_api_calls': 0,
            'failed_api_calls': 0,
            'database_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'circuit_breaker_opens': 0,
            'total_response_time': 0.0
        }
        self.alerts = []
    
    def record_api_call(self, success: bool, response_time: float):
        """Record API call metrics"""
        self.metrics['api_calls'] += 1
        self.metrics['total_response_time'] += response_time
        
        if success:
            self.metrics['successful_api_calls'] += 1
        else:
            self.metrics['failed_api_calls'] += 1
            
        # Check for alerts
        error_rate = self.metrics['failed_api_calls'] / self.metrics['api_calls']
        if error_rate > 0.1:  # 10% error rate threshold
            self.alerts.append({
                'type': 'high_api_error_rate',
                'message': f'API error rate is {error_rate:.2%}',
                'timestamp': time.time()
            })
    
    def record_database_query(self, success: bool):
        """Record database query metrics"""
        self.metrics['database_queries'] += 1
        
        if success:
            self.metrics['successful_queries'] += 1
        else:
            self.metrics['failed_queries'] += 1
    
    def record_circuit_breaker_open(self):
        """Record circuit breaker opening"""
        self.metrics['circuit_breaker_opens'] += 1
        self.alerts.append({
            'type': 'circuit_breaker_open',
            'message': 'Circuit breaker opened due to service failures',
            'timestamp': time.time()
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        avg_response_time = (
            self.metrics['total_response_time'] / self.metrics['api_calls']
            if self.metrics['api_calls'] > 0 else 0
        )
        
        api_error_rate = (
            self.metrics['failed_api_calls'] / self.metrics['api_calls']
            if self.metrics['api_calls'] > 0 else 0
        )
        
        db_error_rate = (
            self.metrics['failed_queries'] / self.metrics['database_queries']
            if self.metrics['database_queries'] > 0 else 0
        )
        
        return {
            **self.metrics,
            'avg_response_time': avg_response_time,
            'api_error_rate': api_error_rate,
            'db_error_rate': db_error_rate,
            'active_alerts': len(self.alerts)
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()

# Package information
__version__ = "1.0.0"
__author__ = "PyIDVerify Development Team"
__description__ = "External service and database integrations with resilience patterns"

# Export public interface
__all__ = [
    # External API integrations (if available)
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
    
    # Database integrations (if available)
    "DatabaseManager",
    "DatabaseConnection",
    "DatabaseConfig",
    "ValidationRecord",
    "AuditRecord",
    "DatabaseType",
    "ConnectionState",
    
    # Factory functions
    "create_integration_client",
    "create_database_manager",
    "create_jumio_client",
    "create_onfido_client",
    "create_credit_bureau_client",
    "create_postgresql_manager",
    "create_mysql_manager",
    "create_sqlite_manager",
    "create_mongodb_manager",
    
    # Utility functions
    "get_available_integrations",
    "health_check_all_integrations",
    "get_recommended_configuration",
    
    # Monitoring
    "IntegrationMonitor"
]

def get_package_info() -> Dict[str, Any]:
    """Get integration package information"""
    return {
        'name': 'pyidverify.integrations',
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'external_apis_available': _EXTERNAL_INTEGRATIONS_AVAILABLE,
        'database_integrations_available': _DATABASE_INTEGRATIONS_AVAILABLE,
        'available_integrations': get_available_integrations(),
        'features': [
            'external_api_clients',
            'database_managers',
            'circuit_breaker_pattern',
            'retry_logic',
            'connection_pooling',
            'health_monitoring',
            'performance_metrics',
            'configuration_management'
        ]
    }
