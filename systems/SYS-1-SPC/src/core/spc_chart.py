import pandas as pd
import numpy as np
import math

from scipy import stats

def _to_plot_values(arr) -> list:
    return [None if pd.isna(v) else float(v) for v in arr]

class SPCchart:
    """
    A class to generate various Statistical Process Control (SPC) chart parameters.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        control_variable: str,
        golden_batches_index: list = None,
        usl=None,
        lsl=None,
        lambda_: float = 0.2,
        l: float = 3,
        target: float = None,
        k: float = 0.5,
        h: float = 5.0,
        alpha=0.05,
    ):
        self.batch_series = data["batch"]
        self.control_df = data.drop(columns=["batch"])
        self.n = self.control_df.shape[0]

        self.golden_batches = (
            self.control_df.iloc[golden_batches_index, :]
            if golden_batches_index is not None
            else self.control_df
        )
        self.subgroup_size = self.control_df.shape[1]

        self.usl = usl
        self.lsl = lsl
        self.lambda_ = lambda_
        self.l = l
        self.target = target
        self.k, self.h = k, h
        self.alpha = alpha

    def imr_plot(self) -> dict:
        """
        Generate I-MR (Individuals and Moving Range) control chart parameters.
        param data (array-like): The input data for which the I-MR chart parameters are calculated.
        return dict: A dictionary containing the mean, UCL, and LCL for both the I chart and the MR chart.
        """
        if self.subgroup_size != 1:
            raise ValueError("Subgroup size must be 1 for I-MR charts.")

        golden_batches = self.golden_batches.to_numpy().flatten()
        # i Chart
        i_mean = golden_batches.mean(axis=0)

        # moving range
        mr = np.abs(np.diff(golden_batches, axis=0))
        mr_mean = np.mean(mr)

        # control limits (常數係數：d2 對應之 3/d2 = 2.66, D4 = 3.27)
        i_ucl = i_mean + 2.66 * mr_mean
        i_lcl = max(0, i_mean - 2.66 * mr_mean)  # LCL 不得小於 0

        mr_ucl = 3.27 * mr_mean
        mr_lcl = 0  # MR chart 的 LCL 永遠是 0

        # For plotting
        all_batches = self.control_df.to_numpy().flatten()
        all_mr = np.abs(np.diff(all_batches, axis=0))

        return {
            "i_chart": {"mean": i_mean, "ucl": i_ucl, "lcl": i_lcl, "values": _to_plot_values(all_batches.tolist())},
            "mr_chart": {"mean": mr_mean, "ucl": mr_ucl, "lcl": mr_lcl, "values": _to_plot_values(all_mr.tolist())},
        }

    def xr_plot(self) -> dict:
        """
        Generate X-bar and R control chart parameters.
        Param data (array-like): The input data for which the X-bar and R chart parameters are calculated.
        Param subgroup_size (int): The size of each subgroup (n).
        Return dict: A dictionary containing the mean, UCL, and LCL for both the X-bar chart and the R chart.
        """

        # 格式: n: (A2, D3, D4)
        CONSTANTS = {
            2: (1.880, 0, 3.267),
            3: (1.023, 0, 2.574),
            4: (0.729, 0, 2.282),
            5: (0.577, 0, 2.114),
            6: (0.483, 0, 2.004),
            7: (0.419, 0.076, 1.924),  # n >= 7 時 D3 不為 0
            8: (0.373, 0.136, 1.864),
            9: (0.337, 0.184, 1.816),
        }

        if self.subgroup_size not in CONSTANTS:
            raise ValueError(
                f"Subgroup size {self.subgroup_size} not supported. Supported sizes: {list(CONSTANTS.keys())}"
            )

        A2, D3, D4 = CONSTANTS[self.subgroup_size]

        # X bar and range
        x_bar = self.golden_batches.mean(axis=1)
        ranges = np.ptp(self.golden_batches, axis=1)

        # central line
        x_barbar = np.mean(x_bar)
        r_bar = np.mean(ranges)

        # control limits
        x_bar_ucl = x_barbar + A2 * r_bar
        x_bar_lcl = x_barbar - A2 * r_bar

        r_ucl = D4 * r_bar
        r_lcl = D3 * r_bar

        # For plotting
        all_batches = self.control_df.mean(axis=1)
        all_r = np.ptp(self.control_df, axis=1)

        return {
            "x_bar_chart": {"mean": x_barbar, "ucl": x_bar_ucl, "lcl": x_bar_lcl, "values": _to_plot_values(all_batches.tolist())},
            "r_chart": {"mean": r_bar, "ucl": r_ucl, "lcl": r_lcl, "values": _to_plot_values(all_r.tolist())},
        }

    def xs_plot(self) -> dict:
        """
        Generate X-s control chart parameters.
        Param data (array-like): The input data for which the X-s chart parameters are calculated.
        Param subgroup_size (int): The size of each subgroup (n).
        Return dict: A dictionary containing the mean, UCL, and LCL for the X-s chart.
        """
        if self.subgroup_size < 2:
            raise ValueError("Subgroup size must be at least 2 for X-s charts.")
        elif self.subgroup_size < 10:
            raise ValueError("must be at least 10 for X-s charts")

        c4 = (
            math.sqrt(2 / (self.subgroup_size - 1))
            * math.gamma(self.subgroup_size / 2)
            / math.gamma((self.subgroup_size - 1) / 2)
        )
        a3 = 3 / c4 * math.sqrt(1 - c4**2)
        b3 = 1 - 3 * c4 / (2 * (self.subgroup_size - 1))
        b4 = 1 + 3 * c4 / (2 * (self.subgroup_size - 1))

        # X bar and standard deviation
        x_bar = self.golden_batches.mean(axis=1)
        s = self.golden_batches.std(axis=1, ddof=1)

        # central line
        x_barbar = np.mean(x_bar)
        s_bar = np.mean(s)

        # control limits
        x_bar_ucl = x_barbar + a3 * s_bar
        x_bar_lcl = x_barbar - a3 * s_bar

        s_ucl = b4 * s_bar
        s_lcl = b3 * s_bar

        # For plotting
        all_batches = self.control_df.mean(axis=1)
        all_s = self.control_df.std(axis=1, ddof=1)
        

        return {
            "x_bar_chart": {"mean": x_barbar, "ucl": x_bar_ucl, "lcl": x_bar_lcl, "values": _to_plot_values(all_batches.tolist())},
            "s_chart": {"mean": s_bar, "ucl": s_ucl, "lcl": s_lcl, "values": _to_plot_values(all_s.tolist())},
        }

    def ewma_plot(self) -> dict:
        if self.subgroup_size != 1:
            golden_batch = self.golden_batches.mean(axis=1).to_numpy().flatten()
            all_batch = self.control_df.mean(axis=1).to_numpy().flatten()
        else:
            golden_batch = self.golden_batches.to_numpy().flatten()
            all_batch = self.control_df.to_numpy().flatten()

        # control limits 用 golden batches 算，nanmean/nanstd 避免 golden 裡也混到缺失值
        mean = np.nanmean(golden_batch)
        sigma = np.nanstd(golden_batch, ddof=1)
        ucl = mean + self.l * sigma * np.sqrt(self.lambda_ / (2 - self.lambda_))
        lcl = mean - self.l * sigma * np.sqrt(self.lambda_ / (2 - self.lambda_))

        # 畫圖用全部批次；遇到缺失值該點留空，遞迴狀態延續前一個有效值
        ewma_values = []
        running = None
        for x in all_batch:
            if pd.isna(x):
                ewma_values.append(None)
                continue
            running = x if running is None else self.lambda_ * x + (1 - self.lambda_) * running
            ewma_values.append(running)

        return {"ewma_values": ewma_values, "mean": mean, "ucl": ucl, "lcl": lcl}


    def cusum_plot(self) -> dict:
        if self.subgroup_size != 1:
            golden_batch = self.golden_batches.mean(axis=1).to_numpy().flatten()
            all_batch = self.control_df.mean(axis=1).to_numpy().flatten()
        else:
            golden_batch = self.golden_batches.to_numpy().flatten()
            all_batch = self.control_df.to_numpy().flatten()

        mu0 = np.nanmean(golden_batch) if self.target is None else self.target

        mr = np.abs(np.diff(golden_batch))
        sigma = np.nanstd(mr, ddof=1) / np.sqrt(2)
        if sigma == 0 or np.isnan(sigma):
            sigma = 1e-10

        allowance = self.k * sigma
        decision_limit = self.h * sigma

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
            "mean": mu0,
            "c_plus": c_plus,
            "c_minus": c_minus,
            "decision_limit": decision_limit,
        }
    

    def spectral_plot(self) -> dict:
        if self.subgroup_size != 1:
            stat_batch = self.golden_batches.mean(axis=1).to_numpy().flatten()
            all_stat = self.control_df.mean(axis=1).to_numpy().flatten()
        else:
            stat_batch = self.golden_batches.to_numpy().flatten()
            all_stat = self.control_df.to_numpy().flatten()

        return {"mean": np.nanmean(stat_batch), "ucl": self.usl, "lcl": self.lsl, "values": _to_plot_values(all_stat.tolist())}
