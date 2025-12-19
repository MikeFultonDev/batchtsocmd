"""
batchtsocmd - Execute TSO and Db2 commands via IKJEFT1B with encoding conversion
"""

__version__ = "0.1.10"
__author__ = "Mike Fulton"

from .main import execute_tso_command, db2cmd, main

__all__ = ["execute_tso_command", "db2cmd", "main"]

# Made with Bob
