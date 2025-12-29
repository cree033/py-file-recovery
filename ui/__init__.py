"""User interfaces"""

from .cli import CLI

try:
    from .gui import GUI
    __all__ = ['CLI', 'GUI']
except ImportError:
    __all__ = ['CLI']

