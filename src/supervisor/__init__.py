"""__init__.py: set NullHandler for any package logs"""

import logging

logger = logging.getLogger(__name__).addHandler(logging.NullHandler())
