"""
batchtsocmd - Execute TSO and Db2 commands via IKJEFT1B with encoding conversion
"""

__version__ = "0.2.0"
__author__ = "Mike Fulton"

from .main import tsocmd, db2sql, db2op, db2bind, db2run, main, version
# Backward-compatibility aliases
from .main import db2cmd, db2admin

__all__ = [
    "tsocmd",
    "db2sql",
    "db2op",
    "db2bind",
    "db2run",
    "main",
    "version",
    "__version__",
    # Deprecated aliases
    "db2cmd",
    "db2admin",
]

# Made with Bob
