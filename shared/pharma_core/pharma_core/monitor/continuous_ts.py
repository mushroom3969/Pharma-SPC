"""Continuous process time-series monitoring methods (nodes H, Q-Q4, R1, S1-S4).

See docs/adr/spc-monitoring-decision-tree.html.
"""

from typing import Any


def arima_residual_monitoring(data: Any) -> Any:
    """Node H: 改走 ARIMA-residual 監控（批次序列本身有自相關）。

    共用下方 determine_differencing_order / determine_arma_order / fit_arima /
    residual_monitoring 這條 pipeline。
    """
    raise NotImplementedError


def determine_differencing_order(data: Any) -> int:
    """Node Q: ADF test，決定差分階數 d。"""
    raise NotImplementedError


def determine_arma_order(data: Any) -> tuple:
    """Node Q1: ACF/PACF，決定 AR/MA 階數。"""
    raise NotImplementedError


def fit_arima(data: Any, order: tuple) -> Any:
    """Node Q2: 配 ARIMA。"""
    raise NotImplementedError


def residual_monitoring(residuals: Any) -> Any:
    """Node Q4: 殘差 I-MR / CUSUM / EWMA（Ljung-Box 通過，殘差為白噪音之後）。"""
    raise NotImplementedError


def cointegration_analysis(data: Any) -> Any:
    """Node R1: Cointegration 分析，取共整合殘差（多變量，非穩態）。"""
    raise NotImplementedError


def pca_mspc_hotelling(data: Any) -> Any:
    """Node S1: PCA MSPC，Hotelling T² + SPE（無 Y，無 dynamic）。"""
    raise NotImplementedError


def dipca_cva_sfa(data: Any) -> Any:
    """Node S2: DiPCA / CVA / SFA（無 Y，有 dynamic）。"""
    raise NotImplementedError


def pls_cpls(data: Any, y: Any) -> Any:
    """Node S3: PLS / CPLS（有 Y，無 dynamic）。"""
    raise NotImplementedError


def dipls(data: Any, y: Any) -> Any:
    """Node S4: DiPLS（有 Y，有 dynamic）。"""
    raise NotImplementedError
