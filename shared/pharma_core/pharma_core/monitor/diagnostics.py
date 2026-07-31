"""Post-alarm root cause diagnostics (node Diag).

See docs/adr/spc-monitoring-decision-tree.html.
"""

from typing import Any


def root_cause_localization(data: Any, alarm: Any) -> Any:
    """Node Diag: 警報後，RBC（relative contribution）根因定位。"""
    raise NotImplementedError
