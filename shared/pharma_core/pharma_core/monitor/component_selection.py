"""Shared component-count selection utility (node CompSel).

Used by pca_mspc, pca_mspc_hotelling, mpca, pls_cpls and other
PC/latent-variable-based methods.

See docs/adr/spc-monitoring-decision-tree.html.
"""

from typing import Any


def select_num_components(data: Any) -> int:
    """Node CompSel: PC/LV 數量選取，CV（PRESS/Q²）+ Parallel Analysis。"""
    raise NotImplementedError
