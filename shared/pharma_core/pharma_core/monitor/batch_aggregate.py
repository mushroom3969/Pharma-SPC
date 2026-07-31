"""Batch aggregate (classical SPC，每批彙整成一個代表值) monitoring methods (nodes H, I1, K1-K3, L, M1, M2).

See docs/adr/spc-monitoring-decision-tree.html.
"""

from typing import Any


def spec_limit_monitoring(data: Any) -> Any:
    """Node I1: Spec limit 監控（初期歷史資料不足）。"""
    raise NotImplementedError


def imr_chart(data: Any) -> Any:
    """Node K1: I-MR chart（subgroup size n=1）。"""
    raise NotImplementedError


def xbar_r_chart(data: Any) -> Any:
    """Node K2: Xbar-R chart（subgroup size n=2~9）。"""
    raise NotImplementedError


def xbar_s_chart(data: Any) -> Any:
    """Node K3: Xbar-S chart（subgroup size n>=10）。"""
    raise NotImplementedError


def ewma_chart(data: Any) -> Any:
    """Node L: EWMA chart（長期小幅偏移）。"""
    raise NotImplementedError


def cusum_chart(data: Any) -> Any:
    """Node L: CUSUM chart（長期小幅偏移）。"""
    raise NotImplementedError


def mewma_chart(data: Any) -> Any:
    """Node M1: MEWMA chart（多變量，少量/中度相關）。"""
    raise NotImplementedError


def mcusum_chart(data: Any) -> Any:
    """Node M1: MCUSUM chart（多變量，少量/中度相關）。"""
    raise NotImplementedError


def pca_mspc(data: Any) -> Any:
    """Node M2: PCA-based MSPC（多變量，多量/高共線）。"""
    raise NotImplementedError
