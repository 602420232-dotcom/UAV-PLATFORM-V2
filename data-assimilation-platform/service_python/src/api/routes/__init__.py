# service_python/src/api/routes/__init__.py

from . import assimilation
from . import batch
from . import monitoring
from . import variance_field

__all__ = ["assimilation", "batch", "monitoring", "variance_field"]
