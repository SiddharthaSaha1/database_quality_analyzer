"""
Helper Utilities for Data Quality Analyzer
Formatting, logging, and JSON serialization.
"""

import json
import logging
from datetime import datetime, date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DataQualityAnalyzer")

class CustomJSONEncoder(json.JSONEncoder):
    """Encodes dates, timestamps, and numpy types to JSON serializable formats."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        try:
            import numpy as np
            if isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, (np.ndarray,)):
                return obj.tolist()
        except ImportError:
            pass
        return super().default(obj)

def serialize_record(record_dict):
    """Safely converts a dictionary of database row values into a compact JSON string."""
    try:
        return json.dumps(record_dict, cls=CustomJSONEncoder)
    except Exception as e:
        return str(record_dict)

def deserialize_record(record_str):
    """Safely parses record JSON back into a Python dict."""
    if not record_str:
        return {}
    try:
        return json.loads(record_str)
    except Exception:
        return {"raw": record_str}

def format_pct(value, decimals=1):
    """Safely formats percentage."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)

