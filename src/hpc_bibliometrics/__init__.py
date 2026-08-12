"""HPC bibliometrics collection and analysis toolkit."""

__version__ = "0.1.0"

# Load audited country extensions after the core registry is defined. Importing
# the package therefore makes the same registry available to analyze/report/CLI.
from . import registry_extra as _registry_extra  # noqa: E402,F401
