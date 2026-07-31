"""Gate functions for the SPC monitoring method decision tree,
plus diagnostic helpers closely tied to a specific gate (e.g. QQ plot
data backing the Node D normality decision).

See docs/adr/spc-monitoring-decision-tree.html for the full diagram.
Most functions correspond to one gate (diamond) node in that diagram;
diagnostic helpers are documented as such and do not affect routing.
"""

import math
from typing import Any, NamedTuple

import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import acf, pacf


def _default_nlags(n: int) -> int:
    """lag 數量的預設公式：min(10*log10(n), n//2 - 1)。

    acorr_ljungbox/acf/pacf 三個函式各自的官方預設公式不同
    （分別是 min(10, n//5)、min(10*log10(n), n-1)、min(10*log10(n), n//2-1)），
    這裡統一取 pacf 的公式（三者中最保守），確保
    has_autocorrelation 與 acf_pacf_data 測的 lag 範圍一致。
    """
    return min(int(10 * math.log10(n)), n // 2 - 1)


def scale_type(metadata: str) -> str:
    """Node A/B/C（合併）：由製程參數的型態 metadata 直接決定分析路徑。

    metadata 是製程參數的型態登記值（由呼叫端查詢 feature 型態表後傳入，
    本函式不查資料庫），預期為 "nominal" / "ordinal" / "continuous" 之一。
    """
    if metadata not in ("nominal", "ordinal", "continuous"):
        raise ValueError(f"scale_type: 未知的型態: {metadata!r}")
    return metadata


class NormalityResult(NamedTuple):
    is_normal: bool
    p_value: float
    statistic: float


def is_normal(data: pd.Series, alpha: float = 0.05) -> NormalityResult:
    """Node D: 常態分布？（Shapiro-Wilk test，alpha 預設 0.05）。

    data 是單一製程參數的歷史數值序列。p-value >= alpha 判定為常態。
    Shapiro-Wilk 在樣本數過大（约 > 5000）時檢定力會下降，屆時需另外評估。

    路由判斷用 .is_normal；p_value/statistic 保留供驗證文件留存紀錄。
    """
    clean = data.dropna()
    if len(clean) < 3:
        raise ValueError("is_normal: 資料筆數不足以進行常態性檢定（至少需要 3 筆）")
    statistic, p_value = stats.shapiro(clean.to_numpy(dtype=float))
    return NormalityResult(
        is_normal=bool(p_value >= alpha),
        p_value=float(p_value),
        statistic=float(statistic),
    )


def qq_plot_data(data: pd.Series) -> dict:
    """Node D 輔助診斷（非路由節點）：算出 QQ plot 所需的數字，不繪圖。

    回傳理論常態分位數 vs 樣本分位數，實際畫圖交給前端或報表層。
    """
    clean = data.dropna()
    if len(clean) < 3:
        raise ValueError("qq_plot_data: 資料筆數不足（至少需要 3 筆）")
    (theoretical_quantiles, sample_quantiles), (slope, intercept, r) = stats.probplot(
        clean.to_numpy(dtype=float), dist="norm"
    )
    return {
        "theoretical_quantiles": theoretical_quantiles.tolist(),
        "sample_quantiles": sample_quantiles.tolist(),
        "fit_line": {"slope": slope, "intercept": intercept, "r": r},
    }


def monitoring_structure(metadata: str) -> str:
    """Node E: 監控結構，由 metadata 直接決定（跟 scale_type 同一套邏輯）。

    metadata 是製程參數的監控結構登記值（由呼叫端查詢 feature 型態表後傳入，
    本函式不查資料庫），預期為 "batch_aggregate" / "batch_trajectory" /
    "continuous_time_series" 之一。

    batch_aggregate：不管一批次採了幾個樣本（subgroup size 可以是 1 或多個），
    最終彙整成一個代表值，在管制圖上是「每批一個點」，批次之間互相比較。
    跟 batch_trajectory 的差別在於：trajectory 是單一批次內、時間軸上的一條
    連續軌跡（例如整批培養過程中每 10 分鐘量一次溫度）。
    """
    valid = ("batch_aggregate", "batch_trajectory", "continuous_time_series")
    if metadata not in valid:
        raise ValueError(f"monitoring_structure: 未知的監控結構: {metadata!r}")
    return metadata


class AutocorrelationResult(NamedTuple):
    has_autocorrelation: bool
    p_value: float
    lags: int


def has_autocorrelation(
    data: pd.Series, lags: int | None = None, alpha: float = 0.05
) -> AutocorrelationResult:
    """Node G: 批次序列本身有自相關？（Ljung-Box test，alpha 預設 0.05）。

    data 是同一製程參數依批次順序排列的數值序列（batch_aggregate 分支）。
    p-value < alpha 判定為顯著自相關，之後應改走 Node H 的 ARIMA-residual 監控。
    lags 未指定時，用 _default_nlags 依樣本數自動決定（跟 acf_pacf_data 一致）。
    """
    clean = data.dropna()
    if lags is None:
        lags = _default_nlags(len(clean))
    if lags < 1 or len(clean) <= lags:
        raise ValueError(
            f"has_autocorrelation: 資料筆數（{len(clean)}）不足以用 lags（{lags}）檢定"
        )
    # lags=[lags]（list，不是整數）讓 acorr_ljungbox 只回傳一列：
    # lag 1~lags 的聯合檢定結果，iloc[0] 取的正是這一列，不是 lag 1 單獨的結果。
    result = acorr_ljungbox(clean.to_numpy(dtype=float), lags=[lags], return_df=True)
    p_value = float(result["lb_pvalue"].iloc[0])
    return AutocorrelationResult(
        has_autocorrelation=bool(p_value < alpha),
        p_value=p_value,
        lags=lags,
    )


def acf_pacf_data(data: pd.Series, nlags: int | None = None, alpha: float = 0.05) -> dict:
    """Node G 輔助診斷（非路由節點）：算出 ACF/PACF plot 所需的數字，不繪圖。

    回傳每個 lag 的 ACF/PACF 值與信賴區間，實際畫圖交給前端或報表層。

    ACF 信賴區間固定用 Bartlett's formula（假設殘差為白噪音，標準誤約 1/√N）；
    PACF 固定用 Yule-Walker adjusted 方法估計。明確指定、不依賴套件預設值，
    避免 statsmodels 版本更新時計算結果悄悄改變。
    nlags 未指定時，用 _default_nlags 依樣本數自動決定（跟 has_autocorrelation 一致）。
    """
    clean = data.dropna()
    if nlags is None:
        nlags = _default_nlags(len(clean))
    if nlags < 1 or len(clean) <= nlags:
        raise ValueError(
            f"acf_pacf_data: 資料筆數（{len(clean)}）不足以用 nlags（{nlags}）計算"
        )
    values = clean.to_numpy(dtype=float)
    acf_values, acf_confint = acf(
        values, nlags=nlags, alpha=alpha, bartlett_confint=True
    )
    pacf_values, pacf_confint = pacf(
        values, nlags=nlags, alpha=alpha, method="ywadjusted"
    )
    return {
        "acf": {
            "values": acf_values.tolist(),
            "confint": acf_confint.tolist(),
        },
        "pacf": {
            "values": pacf_values.tolist(),
            "confint": pacf_confint.tolist(),
        },
    }


def has_sufficient_history(data: pd.Series, min_batches: int = 20) -> bool:
    """Node I: 歷史資料量足夠？（業務規則，非統計檢定；預設至少 20 批，
    SPC 業界常見經驗值 20~25 批）。

    data 是同一製程參數依批次順序排列的數值序列。批次數（扣除缺漏值）
    >= min_batches 才判定為足夠；不足則應先走 Node I1 的 Spec limit 監控。
    """
    return len(data.dropna()) >= min_batches


def shift_type(selection: str) -> str:
    """Node J: 偏移類型，由使用者在介面上選擇（不從資料/metadata 推算）。

    selection 是使用者選擇的分析意圖（由呼叫端傳入，本函式只負責驗證），
    預期為 "short_term_large" / "long_term_small" / "multivariate" 之一。
    """
    valid = ("short_term_large", "long_term_small", "multivariate")
    if selection not in valid:
        raise ValueError(f"shift_type: 未知的偏移類型: {selection!r}")
    return selection


def subgroup_size_category(n: int) -> str:
    """Node K: Subgroup size。

    n 是每個批次（subgroup）採樣的樣本數。回傳 "n_1"（→ I-MR）/
    "n_2_9"（→ Xbar-R）/ "n_ge_10"（→ Xbar-S）之一。
    """
    if n < 1:
        raise ValueError(f"subgroup_size_category: n 必須 >= 1，收到 {n!r}")
    if n == 1:
        return "n_1"
    if n <= 9:
        return "n_2_9"
    return "n_ge_10"


class CollinearityResult(NamedTuple):
    has_high_collinearity: bool
    vif: dict
    correlation_matrix: dict


def has_high_collinearity(data: pd.DataFrame, vif_threshold: float = 10.0) -> CollinearityResult:
    """Node M: 變數共線性（多變量分支，VIF 門檻預設 10）。

    data 是多個製程參數的數值矩陣（欄位＝各參數，列＝各批次）。
    任一變數的 VIF 超過 vif_threshold，即判定整體高共線
    （→ Node M2 PCA-based MSPC；否則 → Node M1 MEWMA/MCUSUM）。
    相關係數矩陣一併回傳供人工複核／畫圖用，不參與判斷本身。
    """
    clean = data.dropna()
    if clean.shape[1] < 2:
        raise ValueError("has_high_collinearity: 至少需要 2 個變數才能計算 VIF")
    if len(clean) <= clean.shape[1]:
        raise ValueError(
            f"has_high_collinearity: 資料筆數（{len(clean)}）需大於變數數"
            f"（{clean.shape[1]}）才能計算 VIF"
        )
    values = clean.to_numpy(dtype=float)
    vif = {
        col: float(variance_inflation_factor(values, i))
        for i, col in enumerate(clean.columns)
    }
    return CollinearityResult(
        has_high_collinearity=any(v > vif_threshold for v in vif.values()),
        vif=vif,
        correlation_matrix=clean.corr().to_dict(),
    )


def batch_length_type(data: pd.DataFrame, unequal_selection: str | None = None) -> str:
    """Node N: 批次等長？（batch_trajectory 分支）。

    data 是長格式 DataFrame，要有 "batch_no"、"time"、"value" 三欄
    （每一列是一個批次在某個時間點的量測值）。"equal" 要求每個批次的
    time 集合完全一致（不只是點數一樣）——點數相同但時間點沒對齊
    （例如一批 t=[0,1,2,3,4]、另一批 t=[0,1.5,2,3,5]）仍視為不等長，
    因為逐點比較還是會比錯時間點，一樣需要對齊。
    若不等長，具體要走 DTW 對齊（N1）還是 FDA 函數表示（N2），由使用者
    透過 unequal_selection 另外選擇（本函式不從資料推算該用哪一種），
    預期為 "unequal_pointwise" / "unequal_functional"。
    """
    required_cols = {"batch_no", "time", "value"}
    missing = required_cols - set(data.columns)
    if missing:
        raise ValueError(f"batch_length_type: 缺少欄位: {missing}")

    time_sets = data.groupby("batch_no")["time"].apply(lambda s: tuple(sorted(s)))
    if time_sets.nunique() == 1:
        return "equal"

    if unequal_selection not in ("unequal_pointwise", "unequal_functional"):
        raise ValueError(
            "batch_length_type: 批次不等長，需指定 unequal_selection 為 "
            f"'unequal_pointwise' 或 'unequal_functional'，收到 {unequal_selection!r}"
        )
    return unequal_selection


def has_multi_phase_structure(metadata: bool) -> bool:
    """Node O0: 批次有明確多相位結構？由使用者/製程知識登記，不從資料推算。

    metadata 是製程是否已知有多個相位（例如生長期、生產期）的登記值，
    由呼叫端傳入，本函式只負責驗證型別。實際相位辨識（多相位建模、找出
    各相位邊界）是 O0a 的工作，不在這裡做。
    """
    if not isinstance(metadata, bool):
        raise ValueError(
            f"has_multi_phase_structure: metadata 必須是 bool，收到 {metadata!r}"
        )
    return metadata


def quality_variable_category(data: Any) -> str:
    """Node O: 有 Y 品質變數？

    回傳 "no_y_linear" / "no_y_nonlinear" / "has_y_linear" / "has_y_drift" 之一。
    """
    raise NotImplementedError


def is_univariate(data: Any) -> bool:
    """Node P: 單變量 / 多變量。"""
    raise NotImplementedError


def is_residual_white_noise(residuals: Any) -> bool:
    """Node Q3: Ljung-Box 檢定，殘差為白噪音？"""
    raise NotImplementedError


def is_stationary(data: Any) -> bool:
    """Node R: ADF 穩態？"""
    raise NotImplementedError


def quality_dynamics_category(data: Any) -> str:
    """Node S: 有 Y？有 dynamic？

    回傳 "no_y_no_dynamic" / "no_y_dynamic" / "has_y_no_dynamic" / "has_y_dynamic" 之一。
    """
    raise NotImplementedError
