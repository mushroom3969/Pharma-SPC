"""Batch trajectory (profile data) monitoring methods (nodes N1, N2, O0a, O1, O1b, O2, O2b).

See docs/adr/spc-monitoring-decision-tree.html.
"""

from typing import Any


def dtw_alignment(data: Any) -> Any:
    """Node N1: DTW / indicator variable 對齊（批次不等長，逐點對齊）。"""
    raise NotImplementedError


def fda_functional_pca(data: Any) -> Any:
    """Node N2: FDA / functional PCA，B-spline 展開係數（批次不等長，函數表示）。"""
    raise NotImplementedError


def multi_phase_model(data: Any) -> Any:
    """Node O0a: 多相位建模——相位辨識 + 各相位局部模型。"""
    raise NotImplementedError


def mpca(data: Any) -> Any:
    """Node O1: MPCA（無 Y，線性）。"""
    raise NotImplementedError


def lstm_autoencoder(data: Any) -> Any:
    """Node O1b: LSTM-autoencoder（無 Y，非線性/長期依賴）。"""
    raise NotImplementedError


def vae(data: Any) -> Any:
    """Node O1b: VAE（無 Y，非線性/長期依賴）。"""
    raise NotImplementedError


def mpls(data: Any, y: Any) -> Any:
    """Node O2: MPLS（有 Y，線性）。"""
    raise NotImplementedError


def jitl_locally_weighted(data: Any, y: Any) -> Any:
    """Node O2b: JITL 局部加權建模（有 Y，緩慢漂移/多重模式）。"""
    raise NotImplementedError
