import pandas as pd
import numpy as np
import math

from scipy import stats

def _to_plot_values(arr) -> list:
    return [None if pd.isna(v) else float(v) for v in arr]

def imr_plot(data: pd.DataFrame, golden_batch_name: list, control_feature: str) -> dict:
    if not golden_batch_name:
        golden_batch_name = data["batch_no"]
    golden_batch = data.loc[data["batch_no"].isin(golden_batch_name), control_feature]

    i_mean = np.mean(golden_batch)
    mr = np.abs(np.diff(golden_batch))
    mr_mean = np.mean(mr)

    i_ucl = i_mean + 2.66 * mr_mean
    i_lcl = max(0, i_mean - 2.66 * mr_mean)
    mr_ucl = 3.27 * mr_mean
    mr_lcl = 0

    return {
        "i_chart": {
            "x": data["batch_no"].tolist(),
            "y": data[control_feature].tolist(),
            "mean": i_mean,
            "ucl": i_ucl,
            "lcl": i_lcl,
        },
        "mr_chart": {
            "x": data["batch_no"].iloc[1:].tolist(),
            "y": np.abs(np.diff(data[control_feature])).tolist(),
            "mean": mr_mean,
            "ucl": mr_ucl,
            "lcl": mr_lcl,
        },
    }


def ewma_plot(data: pd.DataFrame, golden_batch_name: list, control_feature: str, lambda_: float = 0.2, l: float = 3) -> dict:
    if not golden_batch_name:
        golden_batch_name = data["batch_no"]
    golden_batch = data.loc[data["batch_no"].isin(golden_batch_name), control_feature]

    # control limits 用 golden batch 算，nanmean/nanstd 避免 golden 裡也混到缺失值
    mean = np.nanmean(golden_batch)
    sigma = np.nanstd(golden_batch, ddof=1)
    ucl = mean + l * sigma * np.sqrt(lambda_ / (2 - lambda_))
    lcl = mean - l * sigma * np.sqrt(lambda_ / (2 - lambda_))

    # 畫圖用全部批次；遇到缺失值該點留空，遞迴狀態延續前一個有效值
    all_batch = data[control_feature]
    ewma_values = []
    running = None
    for x in all_batch:
        if pd.isna(x):
            ewma_values.append(None)
            continue
        running = x if running is None else lambda_ * x + (1 - lambda_) * running
        ewma_values.append(running)

    return {
        "x": data["batch_no"].tolist(),
        "y": ewma_values,
        "mean": mean,
        "ucl": ucl,
        "lcl": lcl,
    }


def cusum_plot(data: pd.DataFrame, control_feature: str, target: float = None, k: float = 0.5, h: float = 5.0) -> dict:
    all_batch = data[control_feature].to_numpy()

    mu0 = np.nanmean(all_batch) if target is None else target

    mr = np.abs(np.diff(all_batch))
    sigma = np.nanstd(mr, ddof=1) / np.sqrt(2)
    if sigma == 0 or np.isnan(sigma):
        sigma = 1e-10

    allowance = k * sigma
    decision_limit = h * sigma

    c_plus = [0.0]
    c_minus = [0.0]
    running_plus, running_minus = 0.0, 0.0
    for i in range(1, len(all_batch)):
        x = all_batch[i]
        if pd.isna(x):
            c_plus.append(None)
            c_minus.append(None)
            continue
        running_plus = max(0, running_plus + (x - mu0) - allowance)
        running_minus = min(0, running_minus + (x - mu0) + allowance)
        c_plus.append(running_plus)
        c_minus.append(running_minus)

    return {
        "x": data["batch_no"].tolist(),
        "y_c_plus": c_plus,
        "y_c_minus": c_minus,
        "mean": mu0,
        "decision_limit": decision_limit,
    }

