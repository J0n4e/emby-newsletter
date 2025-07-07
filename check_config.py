#!/usr/bin/env python3
"""
Configuration checker script for Emby Newsletter
Run this to test your configuration before running the newsletter
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from configuration import ConfigurationManager
from configuration_checker import ConfigurationChecker

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Check Emby Newsletter configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_config.py                    # Check default config
  python check_config.py -c /path/config   # Check custom config path
  python check_config.py -v                # Verbose output
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='/app/config/config.yml',
        help='Path to configuration file (default: /app/config/config.yml)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--no-connectivity',
        action='store_true',
        help='Skip connectivity tests (only validate configuration structure)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("Emby Newsletter Configuration Checker")
        print("=====================================\n")
        
        # Load configuration
        print(f"Loading configuration from: {args.config}")
        config_manager = ConfigurationManager(args.config)
        config = config_manager.load_config()
        
        print("✅ Configuration file loaded successfully\n")
        
        # Run configuration checks
        checker = ConfigurationChecker(config)
        
        if args.no_connectivity:
            print("Skipping connectivity tests...\n")
            # Only run basic validation (already done in load_config)
            checker._report_results()
            success = len(checker.errors) == 0
        else:
            success = checker.check_all()
        
        if success:
            print("\n🎉 Configuration is ready to use!")
            print("You can now run the newsletter with: python src/main.py")
            return 0
        else:
            print("\n❌ Please fix the configuration errors above before running the newsletter.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nConfiguration check cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Configuration check failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())