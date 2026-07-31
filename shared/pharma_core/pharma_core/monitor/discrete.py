"""Discrete/categorical monitoring methods (nodes C1 / C2).

See docs/adr/spc-monitoring-decision-tree.html.
"""

from typing import Any


def fishers_exact_test(data: Any) -> Any:
    """Node C1: Fisher's exact test（Nominal 無序）。"""
    raise NotImplementedError


def multinomial_cusum(data: Any) -> Any:
    """Node C1: Multinomial CUSUM（Nominal 無序）。"""
    raise NotImplementedError


def category_p_chart(data: Any) -> Any:
    """Node C1: 特定類別 p / np-chart（Nominal 無序）。"""
    raise NotImplementedError


def ordinal_score_cusum_ewma(data: Any) -> Any:
    """Node C2: 指派分數 CUSUM/EWMA（Ordinal 有序）。"""
    raise NotImplementedError


def cumulative_proportion_p_chart(data: Any) -> Any:
    """Node C2: 累積比例 p-chart（Ordinal 有序）。"""
    raise NotImplementedError


def proportional_odds_model(data: Any) -> Any:
    """Node C2: Proportional odds model（Ordinal 有序）。"""
    raise NotImplementedError
