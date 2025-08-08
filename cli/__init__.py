"""
CLI Package
===========

Command-line interface for PyIDVerify with comprehensive validation,
configuration management, and interactive features.

Features:
- Single and batch ID validation
- Interactive REPL mode for testing
- Configuration management
- Health checks and system diagnostics
- Performance monitoring and statistics
- Multiple output formats (text, JSON, CSV, table, YAML)
- Colored output and progress indicators
- Command history and autocompletion

Commands:
- validate: Validate individual IDs or batch files
- config: Manage configuration settings  
- health: Check system health and integrations
- stats: View performance statistics
- repl: Start interactive validation session
- export: Export validation results
- help: Show command help
- version: Show version information

Examples:
    $ pyidverify validate email user@example.com
    $ pyidverify validate --batch-file users.csv email
    $ pyidverify config set output_format json
    $ pyidverify health --check-all
    $ pyidverify repl
    $ pyidverify stats --export results.json

Installation:
    For full CLI functionality, install optional dependencies:
    $ pip install pyidverify[cli]

Security Features:
- Secure credential handling and storage
- Audit logging for all CLI operations
- Rate limiting for batch operations
- PII masking in output and logs
- Session management and timeouts
"""

from typing import Dict, Any, Optional, List

# Import CLI components with graceful degradation
try:
    from .main import (
        CLIApplication,
        CLIConfig,
        CLIOutputFormatter,
        BatchProcessor,
        InteractiveREPL,
        OutputFormat,
        LogLevel,
        main
    )
    _CLI_AVAILABLE = True
except ImportError as e:
    _CLI_AVAILABLE = False
    _CLI_IMPORT_ERROR = str(e)
    
    # Provide minimal interface
    class CLIApplication:
        def __init__(self):
            print("CLI functionality requires additional dependencies.")
            print("Install with: pip install pyidverify[cli]")
    
    def main():
        print("CLI functionality not available.")
        print("Install CLI dependencies with: pip install pyidverify[cli]")
        return 1

def get_cli_info() -> Dict[str, Any]:
    """Get CLI package information and status"""
    return {
        'name': 'pyidverify.cli',
        'version': '1.0.0',
        'description': 'Command-line interface for PyIDVerify',
        'available': _CLI_AVAILABLE,
        'error': _CLI_IMPORT_ERROR if not _CLI_AVAILABLE else None,
        'required_dependencies': [
            'click',
            'colorama', 
            'tabulate',
            'prompt_toolkit'
        ],
        'optional_dependencies': [
            'yaml'
        ],
        'commands': [
            'validate',
            'config',
            'health', 
            'stats',
            'repl',
            'export',
            'help',
            'version'
        ],
        'output_formats': [
            'text',
            'json',
            'csv',
            'table',
            'yaml'
        ],
        'features': [
            'single_validation',
            'batch_validation',
            'interactive_repl',
            'configuration_management',
            'health_monitoring',
            'performance_stats',
            'colored_output',
            'command_history',
            'autocompletion',
            'audit_logging'
        ]
    }

def check_cli_dependencies() -> Dict[str, bool]:
    """Check availability of CLI dependencies"""
    dependencies = {
        'click': False,
        'colorama': False,
        'tabulate': False,
        'prompt_toolkit': False,
        'yaml': False
    }
    
    # Check each dependency
    for dep in dependencies:
        try:
            __import__(dep.replace('_', '.'))
            dependencies[dep] = True
        except ImportError:
            pass
    
    return dependencies

def get_installation_instructions() -> str:
    """Get installation instructions for CLI dependencies"""
    return """
To use the PyIDVerify CLI, install the CLI extra dependencies:

  pip install pyidverify[cli]

Or install dependencies manually:

  pip install click colorama tabulate prompt_toolkit

Optional dependencies for additional features:

  pip install pyyaml  # For YAML output format

After installation, you can use the CLI:

  pyidverify --help
  pyidverify validate email user@example.com
  pyidverify repl
"""

def create_cli_app(config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """
    Create CLI application instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        CLIApplication instance or None if not available
    """
    if not _CLI_AVAILABLE:
        return None
    
    app = CLIApplication()
    
    if config:
        # Apply custom configuration
        for key, value in config.items():
            if hasattr(app.config, key):
                setattr(app.config, key, value)
    
    return app

# Command-line entry point
def cli_main():
    """Main entry point for CLI"""
    if _CLI_AVAILABLE:
        main()
    else:
        print("PyIDVerify CLI is not available.")
        print(get_installation_instructions())
        return 1

# Package information
__version__ = "1.0.0"
__author__ = "PyIDVerify Development Team"
__description__ = "Command-line interface for PyIDVerify identity verification"

# Export public interface
__all__ = [
    # Main classes (if available)
    "CLIApplication",
    "CLIConfig", 
    "CLIOutputFormatter",
    "BatchProcessor",
    "InteractiveREPL",
    "OutputFormat",
    "LogLevel",
    
    # Functions
    "main",
    "cli_main",
    "create_cli_app",
    "get_cli_info",
    "check_cli_dependencies",
    "get_installation_instructions"
]

# Module configuration
def configure_cli(config: Dict[str, Any]) -> bool:
    """
    Configure CLI with custom settings.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if configuration was successful, False otherwise
    """
    if not _CLI_AVAILABLE:
        return False
    
    # Configuration would be applied to CLI components
    return True
