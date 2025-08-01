#!/usr/bin/env python3
"""
Production-ready Shelly Gen4 device scanner and management tool.
Supports discovery, firmware updates, configuration, and monitoring.
"""

from .cli import CLI

def main():
    """Main entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()