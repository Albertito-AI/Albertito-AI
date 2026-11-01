"""Court Submission Integrity: local, bounded submission checks, not adjudication.

Created for Albert Tan Sin Hon. AI-assisted implementation. See RIGHTS.md.
"""
__version__ = "0.1.0a1"
from .engine import InputError, check_submission

__all__ = ["InputError", "check_submission", "__version__"]
