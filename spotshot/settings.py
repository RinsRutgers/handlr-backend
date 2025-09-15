"""
Django settings for spotshot project.

This file is kept for backwards compatibility.
For actual configuration, see the config/ directory:
- config/base.py: Base settings shared across environments
- config/local.py: Local development settings
- config/production.py: Production settings

To use a specific configuration, set DJANGO_SETTINGS_MODULE to:
- spotshot.config.local (for development)
- spotshot.config.production (for production)
"""

# Import local settings by default for backwards compatibility
from .config.local import *
