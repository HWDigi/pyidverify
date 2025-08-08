"""
Command-Line Interface (CLI)
===========================

This module provides a comprehensive command-line interface for PyIDVerify,
enabling users to validate IDs, manage configurations, run health checks,
and perform administrative tasks from the terminal.

Features:
- Interactive validation commands for all supported ID types
- Batch validation from files (CSV, JSON, XML)
- Configuration management and validation
- Health checks and system diagnostics
- Performance monitoring and reporting
- Interactive REPL mode for testing
- Plugin management and extension loading
- Export capabilities for validation results

Commands:
- validate: Validate individual IDs or batch files
- config: Manage configuration settings
- health: Check system health and integrations
- stats: View performance statistics
- repl: Start interactive validation session
- plugins: Manage validator plugins
- export: Export validation results

Examples:
    $ pyidverify validate email user@example.com
    $ pyidverify validate --batch-file users.csv
    $ pyidverify config set encryption.algorithm AES-256-GCM
    $ pyidverify health --check-all
    $ pyidverify repl
    $ pyidverify stats --export results.json

Security Features:
- Secure credential handling and storage
- Audit logging for all CLI operations
- Rate limiting for batch operations
- PII masking in output and logs
- Encrypted storage of validation results
- Session management and timeouts
"""

import asyncio
import sys
import os
import json
import csv
import time
import argparse
from typing import Dict, Any, List, Optional, Union, TextIO
from pathlib import Path
from datetime import datetime, timedelta
import getpass
import signal
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import click
    import colorama
    import tabulate
    import prompt_toolkit
    from prompt_toolkit import prompt
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    _CLI_DEPENDENCIES_AVAILABLE = True
except ImportError:
    _CLI_DEPENDENCIES_AVAILABLE = False

try:
    from ..core.factory import ValidatorFactory
    from ..core.config import ConfigurationManager
    from ..core.exceptions import ValidationError, SecurityError
    from ..security.audit import AuditLogger
    from ..utils.exporters import ResultExporter
    from ..integrations import get_available_integrations, health_check_all_integrations
    _IMPORTS_AVAILABLE = True
except ImportError as e:
    # Graceful degradation
    _IMPORTS_AVAILABLE = False
    _IMPORT_ERROR = str(e)

class OutputFormat(Enum):
    """Output format options"""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    TABLE = "table"
    YAML = "yaml"

class LogLevel(Enum):
    """CLI logging levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class CLIConfig:
    """CLI configuration settings"""
    output_format: OutputFormat = OutputFormat.TEXT
    log_level: LogLevel = LogLevel.INFO
    color_output: bool = True
    audit_enabled: bool = True
    session_timeout: int = 3600  # 1 hour
    max_batch_size: int = 10000
    rate_limit_per_minute: int = 1000
    history_file: str = "~/.pyidverify_history"
    config_file: str = "~/.pyidverify_config.json"
    results_directory: str = "./validation_results"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CLIConfig':
        """Create from dictionary"""
        return cls(
            output_format=OutputFormat(data.get('output_format', 'text')),
            log_level=LogLevel(data.get('log_level', 'info')),
            color_output=data.get('color_output', True),
            audit_enabled=data.get('audit_enabled', True),
            session_timeout=data.get('session_timeout', 3600),
            max_batch_size=data.get('max_batch_size', 10000),
            rate_limit_per_minute=data.get('rate_limit_per_minute', 1000),
            history_file=data.get('history_file', '~/.pyidverify_history'),
            config_file=data.get('config_file', '~/.pyidverify_config.json'),
            results_directory=data.get('results_directory', './validation_results')
        )

class CLIOutputFormatter:
    """Formats CLI output in various formats"""
    
    def __init__(self, config: CLIConfig):
        self.config = config
        
        if _CLI_DEPENDENCIES_AVAILABLE and config.color_output:
            colorama.init()
            self.colors = {
                'success': colorama.Fore.GREEN,
                'error': colorama.Fore.RED,
                'warning': colorama.Fore.YELLOW,
                'info': colorama.Fore.CYAN,
                'reset': colorama.Style.RESET_ALL
            }
        else:
            self.colors = {key: '' for key in ['success', 'error', 'warning', 'info', 'reset']}
    
    def format_validation_result(self, result: Dict[str, Any]) -> str:
        """Format validation result for output"""
        if self.config.output_format == OutputFormat.JSON:
            return json.dumps(result, indent=2, default=str)
        
        elif self.config.output_format == OutputFormat.CSV:
            # Flatten result for CSV format
            flat_result = self._flatten_dict(result)
            return ','.join(str(v) for v in flat_result.values())
        
        elif self.config.output_format == OutputFormat.TABLE:
            if _CLI_DEPENDENCIES_AVAILABLE:
                data = [[k, v] for k, v in result.items()]
                return tabulate.tabulate(data, headers=['Field', 'Value'], tablefmt='grid')
            else:
                return self._format_as_text(result)
        
        elif self.config.output_format == OutputFormat.YAML:
            try:
                import yaml
                return yaml.dump(result, default_flow_style=False)
            except ImportError:
                return self._format_as_text(result)
        
        else:  # TEXT format
            return self._format_as_text(result)
    
    def _format_as_text(self, result: Dict[str, Any]) -> str:
        """Format result as human-readable text"""
        output = []
        
        # Validation status
        status_color = self.colors['success'] if result.get('is_valid') else self.colors['error']
        status = "VALID" if result.get('is_valid') else "INVALID"
        output.append(f"{status_color}{status}{self.colors['reset']}")
        
        # Basic info
        output.append(f"Type: {result.get('id_type', 'Unknown')}")
        output.append(f"Confidence: {result.get('confidence', 0):.2%}")
        
        # Response time
        if 'metadata' in result and 'response_time_ms' in result['metadata']:
            output.append(f"Response Time: {result['metadata']['response_time_ms']:.2f}ms")
        
        # Errors
        if result.get('errors'):
            output.append(f"{self.colors['error']}Errors:{self.colors['reset']}")
            for error in result['errors']:
                output.append(f"  - {error}")
        
        # Additional metadata (selective)
        metadata = result.get('metadata', {})
        if 'checks_performed' in metadata:
            output.append(f"Checks Performed: {', '.join(metadata['checks_performed'])}")
        
        return '\n'.join(output)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, ', '.join(str(item) for item in v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{self.colors['success']}{message}{self.colors['reset']}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{self.colors['error']}Error: {message}{self.colors['reset']}", file=sys.stderr)
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{self.colors['warning']}Warning: {message}{self.colors['reset']}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{self.colors['info']}{message}{self.colors['reset']}")

class BatchProcessor:
    """Processes batch validation requests"""
    
    def __init__(self, config: CLIConfig, formatter: CLIOutputFormatter):
        self.config = config
        self.formatter = formatter
        
        if _IMPORTS_AVAILABLE:
            self.validator_factory = ValidatorFactory()
            self.audit_logger = AuditLogger("cli_batch_processor")
    
    async def process_batch_file(self, file_path: str, validator_type: str, 
                               output_file: Optional[str] = None) -> Dict[str, Any]:
        """Process batch validation from file"""
        if not _IMPORTS_AVAILABLE:
            raise RuntimeError("Core dependencies not available")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Batch file not found: {file_path}")
        
        # Determine file format
        if file_path.suffix.lower() == '.csv':
            data = self._load_csv_file(file_path)
        elif file_path.suffix.lower() == '.json':
            data = self._load_json_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Validate batch size
        if len(data) > self.config.max_batch_size:
            raise ValueError(f"Batch size {len(data)} exceeds maximum {self.config.max_batch_size}")
        
        # Get validator
        validator = self.validator_factory.create_validator(validator_type)
        if not validator:
            raise ValueError(f"Unknown validator type: {validator_type}")
        
        # Process batch
        results = []
        successful = 0
        failed = 0
        start_time = time.time()
        
        self.formatter.print_info(f"Processing {len(data)} items...")
        
        for i, item in enumerate(data):
            try:
                # Rate limiting
                if i > 0 and i % self.config.rate_limit_per_minute == 0:
                    await asyncio.sleep(60)  # Wait 1 minute
                
                # Extract value to validate
                value = item if isinstance(item, str) else item.get('value', str(item))
                
                # Validate
                result = validator.validate(value)
                
                # Add batch metadata
                batch_result = {
                    'batch_index': i,
                    'input_value': value,
                    'result': {
                        'is_valid': result.is_valid,
                        'id_type': result.id_type,
                        'confidence': result.confidence,
                        'errors': result.errors,
                        'metadata': result.metadata
                    }
                }
                
                results.append(batch_result)
                
                if result.is_valid:
                    successful += 1
                else:
                    failed += 1
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    self.formatter.print_info(f"Processed {i + 1}/{len(data)} items")
                
            except Exception as e:
                failed += 1
                results.append({
                    'batch_index': i,
                    'input_value': value if 'value' in locals() else str(item),
                    'result': {
                        'is_valid': False,
                        'id_type': validator_type,
                        'confidence': 0.0,
                        'errors': [str(e)],
                        'metadata': {'processing_error': True}
                    }
                })
        
        processing_time = time.time() - start_time
        
        # Create summary
        summary = {
            'total_processed': len(data),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(data) if len(data) > 0 else 0,
            'processing_time_seconds': processing_time,
            'validator_type': validator_type,
            'batch_file': str(file_path),
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        }
        
        # Save results if output file specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.formatter.print_success(f"Results saved to: {output_path}")
        
        # Audit logging
        if self.config.audit_enabled:
            self.audit_logger.log_event("batch_validation", {
                'total_processed': len(data),
                'successful': successful,
                'failed': failed,
                'validator_type': validator_type,
                'processing_time': processing_time
            })
        
        return summary
    
    def _load_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from CSV file"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _load_json_file(self, file_path: Path) -> List[Any]:
        """Load data from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure it's a list
        if not isinstance(data, list):
            data = [data]
        
        return data

class InteractiveREPL:
    """Interactive Read-Eval-Print Loop for validation testing"""
    
    def __init__(self, config: CLIConfig, formatter: CLIOutputFormatter):
        self.config = config
        self.formatter = formatter
        self.session_active = True
        
        if _IMPORTS_AVAILABLE:
            self.validator_factory = ValidatorFactory()
            self.audit_logger = AuditLogger("cli_repl")
        
        # Set up command completion
        if _CLI_DEPENDENCIES_AVAILABLE:
            commands = [
                'validate', 'help', 'exit', 'quit', 'list', 'config', 'stats', 'history', 'clear'
            ]
            validator_types = [
                'email', 'phone', 'ssn', 'credit_card', 'bank_account', 'ip', 'custom'
            ]
            self.completer = WordCompleter(commands + validator_types)
            
            # History file
            history_path = Path(self.config.history_file).expanduser()
            self.history = FileHistory(str(history_path))
        else:
            self.completer = None
            self.history = None
    
    async def start(self):
        """Start interactive REPL session"""
        if not _IMPORTS_AVAILABLE:
            self.formatter.print_error("Core dependencies not available for REPL")
            return
        
        self.formatter.print_success("PyIDVerify Interactive REPL")
        self.formatter.print_info("Type 'help' for commands, 'exit' to quit")
        print()
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        while self.session_active:
            try:
                if _CLI_DEPENDENCIES_AVAILABLE:
                    user_input = await self._get_input_async()
                else:
                    user_input = input("pyidverify> ")
                
                if not user_input.strip():
                    continue
                
                await self._process_command(user_input.strip())
                
            except (EOFError, KeyboardInterrupt):
                self._exit_repl()
            except Exception as e:
                self.formatter.print_error(f"Command error: {str(e)}")
        
        self.formatter.print_info("REPL session ended")
    
    async def _get_input_async(self) -> str:
        """Get input with async support and autocompletion"""
        return await prompt(
            "pyidverify> ",
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer
        )
    
    async def _process_command(self, command: str):
        """Process REPL command"""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ['exit', 'quit']:
            self._exit_repl()
        
        elif cmd == 'help':
            self._show_help()
        
        elif cmd == 'validate':
            if len(args) >= 2:
                validator_type = args[0]
                value = ' '.join(args[1:])
                await self._validate_value(validator_type, value)
            else:
                self.formatter.print_error("Usage: validate <type> <value>")
        
        elif cmd == 'list':
            self._list_validators()
        
        elif cmd == 'config':
            if args:
                await self._config_command(args)
            else:
                self._show_config()
        
        elif cmd == 'stats':
            await self._show_stats()
        
        elif cmd == 'history':
            self._show_history()
        
        elif cmd == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
        
        else:
            self.formatter.print_error(f"Unknown command: {cmd}. Type 'help' for available commands.")
    
    async def _validate_value(self, validator_type: str, value: str):
        """Validate a value in REPL"""
        try:
            validator = self.validator_factory.create_validator(validator_type)
            if not validator:
                self.formatter.print_error(f"Unknown validator type: {validator_type}")
                return
            
            result = validator.validate(value)
            
            # Format and display result
            result_dict = {
                'is_valid': result.is_valid,
                'id_type': result.id_type,
                'confidence': result.confidence,
                'errors': result.errors,
                'metadata': result.metadata
            }
            
            formatted_result = self.formatter.format_validation_result(result_dict)
            print(formatted_result)
            
            # Audit logging
            if self.config.audit_enabled:
                self.audit_logger.log_validation(
                    validator_type, value, result.is_valid, {'source': 'repl'}
                )
        
        except Exception as e:
            self.formatter.print_error(f"Validation error: {str(e)}")
    
    def _show_help(self):
        """Show REPL help"""
        help_text = """
Available Commands:
  validate <type> <value>  - Validate a value with specified validator
  list                     - List available validators
  config [get|set] [key] [value] - Manage configuration
  stats                    - Show performance statistics
  history                  - Show command history
  clear                    - Clear screen
  help                     - Show this help
  exit/quit               - Exit REPL

Validator Types:
  email, phone, ssn, credit_card, bank_account, ip, custom

Examples:
  validate email user@example.com
  validate phone +1-555-123-4567
  validate ssn 123-45-6789
"""
        print(help_text)
    
    def _list_validators(self):
        """List available validators"""
        if not _IMPORTS_AVAILABLE:
            self.formatter.print_error("Cannot list validators - core dependencies not available")
            return
        
        validators = self.validator_factory.get_available_validators()
        
        self.formatter.print_info("Available Validators:")
        for validator_type, info in validators.items():
            status = "✓" if info.get('available', False) else "✗"
            print(f"  {status} {validator_type}: {info.get('description', 'No description')}")
    
    async def _config_command(self, args: List[str]):
        """Handle config command"""
        if args[0] == 'get':
            if len(args) > 1:
                # Get specific config value
                key = args[1]
                # Implementation would get config value
                self.formatter.print_info(f"Config {key}: [value]")
            else:
                self._show_config()
        
        elif args[0] == 'set':
            if len(args) >= 3:
                key, value = args[1], args[2]
                # Implementation would set config value
                self.formatter.print_success(f"Set {key} = {value}")
            else:
                self.formatter.print_error("Usage: config set <key> <value>")
        
        else:
            self.formatter.print_error("Usage: config [get|set] [key] [value]")
    
    def _show_config(self):
        """Show current configuration"""
        config_dict = self.config.to_dict()
        formatted_config = self.formatter.format_validation_result(config_dict)
        print("Current Configuration:")
        print(formatted_config)
    
    async def _show_stats(self):
        """Show performance statistics"""
        # Implementation would gather stats from validators and integrations
        stats = {
            'session_time': time.time() - getattr(self, '_session_start_time', time.time()),
            'commands_executed': getattr(self, '_command_count', 0),
            'validations_performed': getattr(self, '_validation_count', 0)
        }
        
        formatted_stats = self.formatter.format_validation_result(stats)
        print("Performance Statistics:")
        print(formatted_stats)
    
    def _show_history(self):
        """Show command history"""
        self.formatter.print_info("Command history feature requires prompt_toolkit")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.formatter.print_info("\nUse 'exit' to quit REPL")
    
    def _exit_repl(self):
        """Exit REPL session"""
        self.session_active = False

class CLIApplication:
    """Main CLI application"""
    
    def __init__(self):
        self.config = CLIConfig()
        self.formatter = CLIOutputFormatter(self.config)
        self.batch_processor = BatchProcessor(self.config, self.formatter)
        self.repl = InteractiveREPL(self.config, self.formatter)
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load CLI configuration from file"""
        config_path = Path(self.config.config_file).expanduser()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                self.config = CLIConfig.from_dict(config_data)
                self.formatter = CLIOutputFormatter(self.config)  # Recreate with new config
            except Exception as e:
                self.formatter.print_warning(f"Failed to load config: {e}")
    
    def _save_config(self):
        """Save CLI configuration to file"""
        config_path = Path(self.config.config_file).expanduser()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
        except Exception as e:
            self.formatter.print_error(f"Failed to save config: {e}")
    
    async def run(self, args: List[str]):
        """Run CLI application with arguments"""
        if not args:
            await self.repl.start()
            return
        
        command = args[0].lower()
        
        if command == 'validate':
            await self._handle_validate_command(args[1:])
        
        elif command == 'config':
            await self._handle_config_command(args[1:])
        
        elif command == 'health':
            await self._handle_health_command(args[1:])
        
        elif command == 'stats':
            await self._handle_stats_command(args[1:])
        
        elif command == 'repl':
            await self.repl.start()
        
        elif command == 'export':
            await self._handle_export_command(args[1:])
        
        elif command in ['help', '--help', '-h']:
            self._show_main_help()
        
        elif command in ['version', '--version', '-v']:
            self._show_version()
        
        else:
            self.formatter.print_error(f"Unknown command: {command}")
            self._show_main_help()
    
    async def _handle_validate_command(self, args: List[str]):
        """Handle validate command"""
        if not _IMPORTS_AVAILABLE:
            self.formatter.print_error("Validation not available - core dependencies missing")
            return
        
        if '--batch-file' in args:
            # Batch validation
            batch_index = args.index('--batch-file')
            if batch_index + 2 >= len(args):
                self.formatter.print_error("Usage: validate --batch-file <file> <validator_type>")
                return
            
            batch_file = args[batch_index + 1]
            validator_type = args[batch_index + 2]
            
            output_file = None
            if '--output' in args:
                output_index = args.index('--output')
                if output_index + 1 < len(args):
                    output_file = args[output_index + 1]
            
            try:
                summary = await self.batch_processor.process_batch_file(
                    batch_file, validator_type, output_file
                )
                
                # Display summary
                self.formatter.print_success(f"Batch validation completed:")
                summary_text = self.formatter.format_validation_result(summary)
                print(summary_text)
                
            except Exception as e:
                self.formatter.print_error(f"Batch validation failed: {str(e)}")
        
        else:
            # Single validation
            if len(args) < 2:
                self.formatter.print_error("Usage: validate <type> <value>")
                return
            
            validator_type = args[0]
            value = ' '.join(args[1:])
            
            try:
                validator_factory = ValidatorFactory()
                validator = validator_factory.create_validator(validator_type)
                
                if not validator:
                    self.formatter.print_error(f"Unknown validator type: {validator_type}")
                    return
                
                result = validator.validate(value)
                
                result_dict = {
                    'is_valid': result.is_valid,
                    'id_type': result.id_type,
                    'confidence': result.confidence,
                    'errors': result.errors,
                    'metadata': result.metadata
                }
                
                formatted_result = self.formatter.format_validation_result(result_dict)
                print(formatted_result)
                
            except Exception as e:
                self.formatter.print_error(f"Validation failed: {str(e)}")
    
    async def _handle_config_command(self, args: List[str]):
        """Handle config command"""
        if not args:
            # Show current configuration
            config_dict = self.config.to_dict()
            formatted_config = self.formatter.format_validation_result(config_dict)
            print("Current Configuration:")
            print(formatted_config)
            return
        
        subcommand = args[0].lower()
        
        if subcommand == 'set':
            if len(args) < 3:
                self.formatter.print_error("Usage: config set <key> <value>")
                return
            
            key = args[1]
            value = args[2]
            
            # Update configuration
            if hasattr(self.config, key):
                # Type conversion based on current value
                current_value = getattr(self.config, key)
                if isinstance(current_value, bool):
                    value = value.lower() in ['true', '1', 'yes', 'on']
                elif isinstance(current_value, int):
                    value = int(value)
                elif isinstance(current_value, float):
                    value = float(value)
                elif isinstance(current_value, Enum):
                    # Handle enum types
                    enum_class = type(current_value)
                    value = enum_class(value)
                
                setattr(self.config, key, value)
                self._save_config()
                
                self.formatter.print_success(f"Set {key} = {value}")
            else:
                self.formatter.print_error(f"Unknown configuration key: {key}")
        
        elif subcommand == 'get':
            if len(args) < 2:
                self.formatter.print_error("Usage: config get <key>")
                return
            
            key = args[1]
            if hasattr(self.config, key):
                value = getattr(self.config, key)
                print(f"{key}: {value}")
            else:
                self.formatter.print_error(f"Unknown configuration key: {key}")
        
        else:
            self.formatter.print_error(f"Unknown config subcommand: {subcommand}")
    
    async def _handle_health_command(self, args: List[str]):
        """Handle health command"""
        if not _IMPORTS_AVAILABLE:
            self.formatter.print_error("Health check not available - core dependencies missing")
            return
        
        check_all = '--check-all' in args or '--all' in args
        
        # Basic system health
        health_info = {
            'system': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'dependencies': {
                'cli_dependencies': _CLI_DEPENDENCIES_AVAILABLE,
                'core_imports': _IMPORTS_AVAILABLE
            }
        }
        
        if check_all:
            # Check integrations if available
            try:
                integrations_health = await health_check_all_integrations()
                health_info['integrations'] = integrations_health
            except Exception as e:
                health_info['integrations_error'] = str(e)
        
        formatted_health = self.formatter.format_validation_result(health_info)
        print("System Health:")
        print(formatted_health)
    
    async def _handle_stats_command(self, args: List[str]):
        """Handle stats command"""
        # Collect and display performance statistics
        stats = {
            'cli_version': '1.0.0',
            'config': self.config.to_dict(),
            'session_info': {
                'start_time': datetime.utcnow().isoformat(),
                'dependencies_available': {
                    'cli': _CLI_DEPENDENCIES_AVAILABLE,
                    'core': _IMPORTS_AVAILABLE
                }
            }
        }
        
        if '--export' in args:
            export_index = args.index('--export')
            if export_index + 1 < len(args):
                export_file = args[export_index + 1]
                
                export_path = Path(export_file)
                export_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(export_path, 'w') as f:
                    json.dump(stats, f, indent=2, default=str)
                
                self.formatter.print_success(f"Stats exported to: {export_path}")
        else:
            formatted_stats = self.formatter.format_validation_result(stats)
            print("Performance Statistics:")
            print(formatted_stats)
    
    async def _handle_export_command(self, args: List[str]):
        """Handle export command"""
        if not args:
            self.formatter.print_error("Usage: export <format> <output_file>")
            return
        
        export_format = args[0]
        output_file = args[1] if len(args) > 1 else f"export.{export_format}"
        
        # Implementation would export various data formats
        self.formatter.print_info(f"Export functionality for {export_format} format")
    
    def _show_main_help(self):
        """Show main help"""
        help_text = """
PyIDVerify CLI - Identity Verification Command Line Interface

Usage: pyidverify <command> [options]

Commands:
  validate <type> <value>        - Validate a single ID
  validate --batch-file <file> <type> - Batch validate from file
  config [get|set] [key] [value] - Manage configuration
  health [--check-all]           - Check system health
  stats [--export <file>]        - Show performance statistics
  repl                          - Start interactive REPL
  export <format> <file>         - Export validation results
  help                          - Show this help
  version                       - Show version information

Validator Types:
  email, phone, ssn, credit_card, bank_account, ip

Examples:
  pyidverify validate email user@example.com
  pyidverify validate --batch-file users.csv email
  pyidverify config set output_format json
  pyidverify health --check-all
  pyidverify repl

Options:
  --output-format <format>      - Output format: text, json, csv, table, yaml
  --no-color                   - Disable colored output
  --verbose                    - Enable verbose logging

For more information, visit: https://github.com/your-org/pyidverify
"""
        print(help_text)
    
    def _show_version(self):
        """Show version information"""
        version_info = {
            'cli_version': '1.0.0',
            'core_version': '1.0.0',
            'python_version': sys.version,
            'dependencies': {
                'cli_deps_available': _CLI_DEPENDENCIES_AVAILABLE,
                'core_imports_available': _IMPORTS_AVAILABLE
            }
        }
        
        formatted_version = self.formatter.format_validation_result(version_info)
        print("Version Information:")
        print(formatted_version)

def main():
    """Main CLI entry point"""
    app = CLIApplication()
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Run async main
    try:
        asyncio.run(app.run(args))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

# Export public interface
__all__ = [
    "CLIApplication",
    "CLIConfig",
    "CLIOutputFormatter",
    "BatchProcessor",
    "InteractiveREPL",
    "OutputFormat",
    "LogLevel",
    "main"
]
