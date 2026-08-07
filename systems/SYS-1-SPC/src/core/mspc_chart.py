import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats as scipy_stats


class pca_based_monitor:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def pca_preprocessing(self, features: list, rows: list, train_set: list) -> dict:
        features = [f for f in features if f != "batch_no"]
        filtered_df = self.data.loc[self.data["batch_no"].isin(rows), ["batch_no"] + features]
        train_df = filtered_df[filtered_df["batch_no"].isin(train_set)]

        return {
            "features": features,  # 清理過的版本，之後都用這個，不要用呼叫端原始傳進來的
            "all": {
                "batch_no": filtered_df["batch_no"].tolist(),
                "features": filtered_df[features].to_dict(orient="records"),
            },
            "train": {
                "batch_no": train_df["batch_no"].tolist(),
                "features": train_df[features].to_dict(orient="records"),
            },
        }


    def parallel_analysis(self, features: list, rows: list, train_set: list, n_iter: int = 100, percentile: float = 95, random_state=None) -> dict:
        prepped = self.pca_preprocessing(features, rows, train_set)
        train_X = pd.DataFrame(prepped["train"]["features"])
        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train_X)
        n_train, n_features = train_scaled.shape

        pca_full = PCA(n_components=min(n_train, n_features))
        pca_full.fit(train_scaled)
        real_eigenvalues = pca_full.explained_variance_

        rng = np.random.default_rng(random_state)
        simulated_eigenvalues = np.zeros((n_iter, len(real_eigenvalues)))
        for i in range(n_iter):
            random_data = rng.standard_normal((n_train, n_features))
            pca_random = PCA(n_components=min(n_train, n_features))
            pca_random.fit(random_data)
            simulated_eigenvalues[i, :] = pca_random.explained_variance_

        threshold = np.percentile(simulated_eigenvalues, percentile, axis=0)
        significant = real_eigenvalues > threshold
        n_components = len(real_eigenvalues) if significant.all() else int(np.argmax(~significant))

        return {
            "n_components": n_components,
            "real_eigenvalues": real_eigenvalues.tolist(),
            "simulated_threshold": threshold.tolist(),
        }

    def fit(self, features: list, rows: list, train_set: list, n_components: int, alpha: float = 0.05):
        if n_components < 1:
            raise ValueError(f"n_components 必須至少為 1，目前算出來是 {n_components}——可能是樣本數太少或特徵有缺失值")
        prepped = self.pca_preprocessing(features, rows, train_set)
        self.features = prepped["features"]  # 改成用清理過的這份
        train_X = pd.DataFrame(prepped["train"]["features"])
        all_X = pd.DataFrame(prepped["all"]["features"])

        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train_X)
        all_scaled = scaler.transform(all_X)
        n_train, n_features = train_scaled.shape

        max_possible = min(n_train, n_features)
        if n_components > max_possible - 1:
            raise ValueError(
                f"n_components={n_components} 太大——訓練批次數 {n_train}、特徵數 {n_features}，"
                f"最多只能設到 {max_possible - 1}（需要保留至少 1 個成分給 SPE 界限計算用）"
            )

        pca_full = PCA(n_components=min(n_train, n_features))
        pca_full.fit(train_scaled)
        eigenvalues = pca_full.explained_variance_

        k = n_components
        retained_eigenvalues = eigenvalues[:k]
        discarded_eigenvalues = eigenvalues[k:]
        loadings = pca_full.components_[:k]

        all_scores = all_scaled @ loadings.T
        t2 = np.sum((all_scores ** 2) / retained_eigenvalues, axis=1)
        reconstructed = all_scores @ loadings
        spe = np.sum((all_scaled - reconstructed) ** 2, axis=1)

        t2_ucl = (k * (n_train - 1) / (n_train - k)) * scipy_stats.f.ppf(1 - alpha, k, n_train - k)
        theta1, theta2, theta3 = (np.sum(discarded_eigenvalues ** p) for p in (1, 2, 3))
        h0 = 1 - (2 * theta1 * theta3) / (3 * theta2 ** 2)
        c_alpha = scipy_stats.norm.ppf(1 - alpha)
        spe_ucl = theta1 * (
            (c_alpha * np.sqrt(2 * theta2 * h0 ** 2) / theta1) + 1 + (theta2 * h0 * (h0 - 1)) / theta1 ** 2
        ) ** (1 / h0)

        # 存起來給下面的畫圖方法共用，不用重新 fit
        self.features = features
        self.n_components = k
        self.explained_variance_ratio_full = pca_full.explained_variance_ratio_
        self.eigenvalues = retained_eigenvalues
        self.loadings = loadings
        self.all_batch_no = prepped["all"]["batch_no"]
        self.all_scaled = all_scaled
        self.all_scores = all_scores
        self.t2, self.t2_ucl = t2, float(t2_ucl)
        self.spe, self.spe_ucl = spe, float(spe_ucl)
        
        return self

    def scree_plot_data(self) -> dict:
        ratio = self.explained_variance_ratio_full
        return {
            "component": list(range(1, len(ratio) + 1)),
            "explained_variance_ratio": ratio.tolist(),
            "cumulative_variance_ratio": np.cumsum(ratio).tolist(),
        }

    def score_plot_data(self, pc_x: int = 1, pc_y: int = 2) -> dict:
        return {
            "batch_no": self.all_batch_no,
            "x": self.all_scores[:, pc_x - 1].tolist(),
            "y": self.all_scores[:, pc_y - 1].tolist(),
            "x_label": f"PC{pc_x}",
            "y_label": f"PC{pc_y}",
        }

    def loading_plot_data(self, pc_x: int = 1, pc_y: int = 2) -> dict:
        return {
            "feature": self.features,
            "x": self.loadings[pc_x - 1, :].tolist(),
            "y": self.loadings[pc_y - 1, :].tolist(),
            "x_label": f"PC{pc_x} loading",
            "y_label": f"PC{pc_y} loading",
        }

    def t2_plot_data(self) -> dict:
        return {"x": self.all_batch_no, "y": self.t2.tolist(), "ucl": self.t2_ucl}

    def spe_plot_data(self) -> dict:
        return {"x": self.all_batch_no, "y": self.spe.tolist(), "ucl": self.spe_ucl}

    def contribution_plot_data(self, batch_no: str) -> dict:
        idx = self.all_batch_no.index(batch_no)
        x_scaled = self.all_scaled[idx, :]
        scores = self.all_scores[idx, :]

        # T^2 貢獻：每個特徵對這個樣本 T^2 的貢獻量
        t2_contribution = np.zeros(len(self.features))
        for k in range(self.n_components):
            t2_contribution += (scores[k] / self.eigenvalues[k]) * self.loadings[k, :] * x_scaled

        # SPE 貢獻：每個特徵的殘差平方（重建不回去的部分）
        reconstructed = scores @ self.loadings
        spe_contribution = (x_scaled - reconstructed) ** 2

        return {
            "batch_no": batch_no,
            "feature": self.features,
            "t2_contribution": t2_contribution.tolist(),
            "spe_contribution": spe_contribution.tolist(),
        }


