# PHARMA-ANALYTICS 專案流程手冊

*給新人與主管*

## 目錄

- [00 · 這份文件是什麼](#00--這份文件是什麼)
- [01 · 角色分工地圖](#01--角色分工地圖)
- [02 · 環境統一方式](#02--環境統一方式)
- [03 · 專案啟動前 Checklist](#03--專案啟動前-checklist)
- [04 · 案件分流判斷](#04--案件分流判斷)
- [05 · Explore 型](#05--explore-型)
- [06 · Analyses 型](#06--analyses-型)
- [07 · Systems 型（常態系統）](#07--systems-型常態系統)
- [08 · ML 型（含模型）](#08--ml-型含模型)
- [09 · API 觸發路徑](#09--api-觸發路徑)
- [10 · 排程／自動觸發路徑](#10--排程自動觸發路徑)
- [11 · Testing & Validation 總表](#11--testing--validation-總表)
- [12 · Git 使用規則](#12--git-使用規則)
- [13 · Branch 規則](#13--branch-規則)

---

## 00 · 這份文件是什麼

這是 `architecture-onboarding.html`（為什麼這樣設計）的操作延伸——那份講「為什麼」，這份講**「輪到你時，實際先做什麼、後做什麼、誰做什麼」**。新人可以照著自己角色的章節動手實作；主管可以只看每節開頭的流程圖跟表格，掌握整體節奏跟卡點在哪。

> **跟 onboarding 文件的分工**
> 資料夾為什麼這樣分、Rule of Three、SBD 邊界等判斷準則，請看 `architecture-onboarding.html`。這份手冊不重複那些理由，只講「順序」與「誰」。

---

## 01 · 角色分工地圖

一人團隊目前是 DS+後端一人身兼多職，但下面用「職務」而不是「人」來切，方便未來實際分工給不同人時，職責邊界不需要重畫。

| 角色 | 負責範圍 |
|---|---|
| **Data Engineer** | `pipeline/` 全部（models/seeds/tests/scripts）；維護 `infra/migrations/` 的執行（設計仍是 ★DS+後端）；pipeline 的 CI 測試（generic + singular） |
| **DS + 後端** | `explore/` `analyses/` 全部；`systems/SYS-N/src/{main.py,core,orchestration,schema.py,router.py,service.py}`；`ml/` 全部；`infra/migrations/` 設計；驗證文件（URS/FS/DS/TM） |
| **前端** | `systems/SYS-N/src/frontend/`；只消費 `schema.py` 鎖死的 API，不猜格式；UAT 操作腳本協助（PQ） |
| **Model Monitoring** | `monitoring/drift/`；`ml/evaluation/` `ml/model_cards/` 的持續追蹤；只建 Issue，重訓決策交回 DS+後端 |

> **現況**：目前 DS+後端一人涵蓋 DS+後端與 Model Monitoring 兩個職能；Data Engineer 是 ⚡ AI 輔助＋人工 review；前端目前尚未建立（`frontend/package.json` 不存在），`setup.sh` 會自動偵測並跳過。

---

## 02 · 環境統一方式

整個 repo 沒有「一個環境打天下」——每個資料夾用途不同、依賴不同，統一的地方是**安裝順序跟入口點只有一個**：根目錄的 `./setup.sh`。

```bash
# 從 repo 根目錄執行，一次裝好全部環境
./setup.sh
```

| 順序 | 環境 | 對應資料夾 | 負責角色 | 啟用方式 |
|---|---|---|---|---|
| 1 | Poetry（`shared/pharma_core`） | `shared/` | DS+後端 | `cd shared/pharma_core && poetry install` |
| 2 | Conda（`pharma-ds`，含 Jupyter kernel） | `explore/ analyses/ ml/` | DS+後端 / Monitoring | `conda activate pharma-ds` |
| 3 | Poetry（systems/SYS-N，in-project venv） | `systems/SYS-N/` | DS+後端 | `cd systems/SYS-N && poetry run uvicorn src.main:app` |
| 4 | Poetry（pipeline，in-project venv） | `pipeline/` | Data Engineer | `cd pipeline && poetry run dbt run` |
| 5 | npm／pnpm（有 package.json 才裝） | `systems/SYS-N/src/frontend/` | 前端 | `pnpm dev` |

> **為什麼 pharma_core 最先裝**
> conda 環境跟每個 systems/SYS-N 的 poetry 環境都會用 `develop = true` / `pip install -e` 的方式引用它，順序反過來會直接裝失敗。

> **已知環境坑**
> Poetry 環境常被 shell 裡殘留的 `VIRTUAL_ENV`／`CONDA_PREFIX` 污染，導致 `poetry run` 悄悄用錯 Python。下指令前先 `unset VIRTUAL_ENV CONDA_PREFIX` 是目前的固定解法。

---

## 03 · 專案啟動前 Checklist

不管接下來是哪一種案件類型，開工前這幾件事要先成立，否則後面任何一個角色都無法真正開始。

- [ ] **DB 可連線** — `infra/migrations/` 已跑過最新版本，本機 `.env` 已依 `infra/.env.example` 填好
- [ ] **`./setup.sh` 跑過一次成功** — 五個環境都裝完，沒有卡在中途
- [ ] **CI 骨架存在** — `.github/workflows/ci.yml` 至少能跑 pytest，即使還很陽春
- [ ] **已決定案件類型** — explore／analyses／systems／ml，決定依據看下一節
- [ ] **（若為 systems/ml 型）schema.py 的責任人已確認** — 開工前先講好誰鎖 API contract

---

## 04 · 案件分流判斷

同一個問題，走錯 Track 是最常見的浪費——不是每件事都要走完整 V-Model，也不是每件事都能隨便交差。

```
新問題進來 → 這會長期重複用嗎？
  否 → explore/（先亂試，沒人審查）→ 值得交付？
    是 → analyses/ 一份 AR 報告，結案

  是，會長期重複用，且會影響製程放行判斷 → Systems 型
    走完整 pipeline + systems/SYS-N → 邏輯是訓練出來的？
      是 → 額外走 ML 型（05-08 節）
```

> **explore／analyses 一定要先建 pipeline 嗎？**
> **不是必要的。** 如果資料乾淨、來源單一，只是要快速看一眼或做一次性判斷，`explore/` 可以直接 `pd.read_excel()`／`pd.read_csv()` 讀原始檔案；`analyses/` 也有自己的 `data/raw/`（唯讀）放這次用到的原始檔案副本，完全不需要碰 dbt——這正是 Track A 刻意設計得輕量的原因。
>
> 但如果資料本身是**多來源、格式彼此不一致**（欄位命名、批號格式都不同，需要 join／去重／對照表），即使還在 explore 階段，先透過 pipeline 建好 staging→intermediate→mart 往往比在 notebook 裡重複寫清洗邏輯更省力——這是實務取捨，不是規則要求。真正「一定要進 pipeline」的分界線只有一個：這個分析預期會**長期重複用、或影響製程放行判斷**，升級成 Systems 型的那一刻，因為 systems/SYS-N 的驗證範圍是從 mart table 開始算的（SBD 邊界），不能繞過。

---

## 05 · Explore 型

`角色：DS+後端 單人`

沒有分工，沒有正式測試。目的是快速驗證一個想法值不值得往下走。

**STEP 1 — 建立 `explore/YYYYMM_[主題]/`**
在 conda `pharma-ds` 環境下開一份 notebook，直接對 mart 查資料、試想法。可以失敗、可以留著雜亂的程式碼。

> 結束條件：得到「這個方向有沒有搞頭」的答案即可，不需要能重現、不需要文件。

---

## 06 · Analyses 型

`角色：DS+後端 單人`

一次性交付，做完就結束，不會有人長期維護。

**STEP 1 — 把 explore/ 裡驗證過的判斷，寫成 `analyses/YYYYMM_[主題]/AR-YYYYMM-[主題].md`**
複製的是「判斷」，不是 notebook 本身。原始資料放 `data/raw/`，唯讀。

> 驗證：內部自我覆核或找同事讀一次報告的方法與數字是否站得住腳——不需要 URS/FS/DS/TM。

---

## 07 · Systems 型（常態系統）

`角色：跨角色`

影響製程放行判斷、要長期維運的工具都走這條路。下面依實際開發順序排列，每個 phase 標出負責角色。

| Phase | 內容 | 負責角色 | 產出 / 檔案 | 驗證 |
|---|---|---|---|---|
| **0** | DB schema 基線 — 用 Alembic 確認 `infra/migrations/` 已有這個系統需要的表結構，沒有就先補 migration | DS+後端 | — | IQ：schema 版本正確、可連線 |
| **1** | pipeline 三層建模 — 新資料源的 staging → intermediate → mart，異常輸入測試案例由 Data Engineer 設計並跟 DS+後端 review | Data Engineer | `pipeline/models/{staging,intermediate,mart}/`, `tests/singular/` | dbt generic tests + 跟原始檔案逐筆核對 |
| **2** | core 統計邏輯 — 純函式，只管算。此時前端與 Data Engineer 都還不需要涉入 | DS+後端 | `systems/SYS-N/src/core/` | OQ：已知輸入→預期輸出單元測試 |
| **3** | schema.py 鎖死 — API contract 定案，**前端從這一刻才能開始動工**，不能提前用猜的 | DS+後端 | — | schema 本身即是前後端的契約測試基準 |
| **4** | orchestration + service.py — 讀 mart → 呼叫 core → 整理成 router 可直接回傳的形狀 | DS+後端 | — | OQ：整合測試、端對端流程 |
| **5** | main.py + router.py（DS+後端）｜ frontend（前端）並行 | DS+後端 ｜ 前端 | `systems/SYS-N/src/{main.py,router.py}` | PQ：`tests/uat/` 操作腳本＋簽核，含前端 UI |
| **6** | 文件收尾 — TM 追溯矩陣（URS↔tests）、docs/adr 記下關鍵取捨，VSR 彙整放行 | DS+後端 | — | TM 不可省略，是稽核追溯鏈的關鍵 |

> **PHASE 5 補充**
> `main.py` 建立 `app = FastAPI()`，把 router 用 `include_router()` 掛進去——這是 FastAPI 真正被實例化的地方，也是 `poetry run uvicorn src.main:app` 指向的進入點；`router.py` 則用 schema 定義的 Pydantic model 接路由。前端同時間開始開發，兩邊只靠 schema 這份契約溝通，不用互相等對方寫完。

---

## 08 · ML 型（含模型）

`角色：DS+後端主導，Monitoring 接手上線後`（Systems 型之上，額外疊加）

當 Phase 2 的 core 邏輯不是寫死公式，而是「訓練出來的」，在 Phase 2 之前多插入這一段。

| Step | 內容 | 角色 | 驗證 |
|---|---|---|---|
| **A** | `ml/features` — 直接讀 `pipeline/models/mart/`，不碰 raw——跟 systems 的 SBD 邊界原則一致 | DS+後端 | — |
| **B** | `ml/experiments → ml/training` — 試驗階段可以亂調參數（MLflow 自動記錄）；方法確定後寫成可重現腳本，訓練產出註冊進 MLflow Registry（狀態：Staging） | DS+後端 | 時間序列資料強制 walk-forward split，禁止 random split |
| **C** | `ml/evaluation + ml/model_cards` — 效能報告（RMSE/AUC/FPR 等）與 Model Card（訓練範圍、效能指標、已知限制）齊備，才能人工核准把 Registry 狀態切到 Production | DS+後端 | Model Card 缺項 = 無法通過驗證放行 |
| **D** | `orchestration/model_loader.py` 接回系統 — 只認 Registry 裡標記 Production 的版本，換模型變成 Registry 操作，不需要改系統程式碼、不需要重新部署 | DS+後端 | — |
| **E（上線後常駐）** | `monitoring/drift/psi_check.py` — 排程比對即時特徵分布跟訓練基準，PSI 超過門檻（通常 0.2）只建 Issue 通知 | Model Monitoring | 重訓決策與執行永遠回到 STEP B 由 DS+後端人工觸發，monitoring 本身**不能**啟動 training——EU Annex 22 禁止線上自動學習 |

---

## 09 · API 觸發路徑

使用者或前端點下一個動作，到看到結果，中間實際發生的順序：

```
前端 / 呼叫端 (送出 HTTP request)
  → router.py (依 schema.py 驗證請求格式)
  → service.py (執行業務邏輯)
  → orchestration (讀 mart，需要時呼叫 model_loader.py)
  → core (純計算，回傳結果)
  → schema.py (驗證回應格式)
  → 前端渲染 (不重新計算任何數字)
```

> **請求在哪裡被擋下**
> 格式不對的請求在 `router.py` 這一關就被 schema 擋掉，根本不會碰到 `core/`——這是 schema 先鎖死帶來的好處：錯誤發生的位置離「真正算數字」的地方越遠越好。

> **main.py 不在這條請求流程裡**
> `main.py`（建立 `app = FastAPI()`、掛上 router）只在服務**啟動時**執行一次，不是每個請求都會經過的步驟，所以沒畫進上面的流程圖——但它是 `uvicorn src.main:app` 真正啟動的進入點，沒有它 router.py 定義的路由不會被任何人接住。

---

## 10 · 排程／自動觸發路徑

不是所有事都等使用者發請求才發生——資料要定期更新、模型要定期盯著有沒有漂移，這些是排程觸發，走的程式碼路徑其實跟 API 路徑共用，只是起點不同。

```
排程器 (cron / CI 排程 workflow)
  → pipeline 重建 (load_*.py 增量載入 → dbt run)
  → mart 更新 (下游系統讀到最新資料)

排程器 (獨立時程，通常較低頻)
  → monitoring/drift (比對即時分布 vs 訓練基準)
  → 超過門檻？ 是 → 建 GitHub Issue，絕不自動重訓
```

如果某個 systems/SYS-N 本身也需要「不等使用者、定期整批算一次」（例如每晚重跑全批次 SPC 檢查），走的是**同一套 orchestration → core**，差別只在觸發源是排程器而不是 `router.py` 收到的 HTTP request——程式碼不用為了排程另外寫一份。

> **排程本身也要被驗證**
> 「排程掛掉了但沒人發現」是最容易被忽略的失敗模式。`dbt run` 失敗、drift 腳本沒跑起來，都要有告警機制通知到人，而不是靜默失敗。

---

## 11 · Testing & Validation 總表

把前面所有流程的驗證方式彙整成一張表，交接或稽核時可以直接照表核對。

| 流程 | 負責角色 | 測試／驗證方式 | 對應階段 |
|---|---|---|---|
| Explore | DS+後端 | 無正式測試，內部合理性檢查 | Track A（不適用 V-Model） |
| Analyses（AR 報告） | DS+後端 | 自我或同儕覆核方法與數字 | Track A |
| pipeline（staging/int/mart） | Data Engineer | dbt generic tests + singular 異常輸入測試 + 跟來源檔案逐筆核對 | IQ 前置 |
| core | DS+後端 | 已知輸入→預期輸出單元測試 | OQ |
| orchestration + API | DS+後端 | 整合測試、schema 契約測試、端對端流程 | OQ |
| frontend | 前端 | UAT 操作腳本＋簽核 | PQ |
| ml/training | DS+後端 | Walk-forward split 評估、Model Card 完整性 | ML 模型驗證 |
| monitoring/drift | Monitoring | 人工製造 drift 確認真的觸發 Issue；確認不會自動重訓 | 上線後持續監控 |
| 排程本身 | Data Engineer / Monitoring | 排程失敗要能通知到人（非靜默失敗） | 維運 |
| 全流程追溯 | DS+後端 | TM 矩陣：URS 需求編號 ↔ tests/ 案例編號 | VSR 放行閘口 |

---

## 12 · Git 使用規則

目前 repo 裡的 commit 訊息還很隨性（`fix`、`sys1 structure buildimg`、`Dev build`），下面是往後統一的規則，不強求回頭整理舊的。

### Commit 訊息慣例

```
格式：<type>(<scope>): 一句話說明做了什麼

type 可用：feat / fix / pipeline / ml / docs / chore / test
scope 通常是資料夾名稱，例如：

pipeline(mart): 修正 batch_no 與 batch_date 年份不一致的解析邏輯
feat(sys-1): 新增 EWMA 管制圖端點
docs(adr): 記錄改用固定管制界限而非時變公式的原因
```

> **★ Zone 的 commit 多一個要求**
> 改到 `core/`、`schema.py`、`infra/migrations/` 這幾個高風險資料夾時，commit 訊息要簡短交代**為什麼**改（不只是改了什麼）——半年後回頭查、或稽核員問起，這行字比重新回想省事得多。

### Notebook（.ipynb）

`.gitattributes` 已設定 `filter=nbstripout`，commit 前會自動清掉 notebook 的執行輸出（圖表、print 結果），讓 diff 只看得到程式碼本身變化。但這個 filter **不會自動生效**，每個人 clone 下來後要自己註冊一次：

```bash
# 在 conda pharma-ds 環境下執行一次即可，往後每次 commit 自動套用
conda activate pharma-ds
nbstripout --install
```

### Secrets 不進版控

- **pipeline/profiles.yml**、**.env** 已在 `.gitignore` 排除——複製時對照 `infra/.env.example` 手動建立，絕不能把真實密碼、連線字串加進暫存區
- 如果不小心 commit 了 secret，不是改下一個 commit 蓋掉就結束——真正的密碼要立刻在源頭（DB／MLflow／API）重新產生，git 歷史裡留過的內容視為已外流

### 已推送的歷史不竄改

分支一旦 push 到遠端（尤其合併進 `main` 之後），不對它做 `rebase`／`force-push`——GxP 稽核追溯要求「這段邏輯是誰寫的、什麼時候改的」要能被完整還原，改寫歷史等於讓這條追溯鏈斷掉。`infra/migrations/` 尤其嚴格：既有的 migration 檔案內容一旦合併，不能回頭修改，發現錯誤要新增下一個版本的 migration 去修正，而不是竄改舊檔案。

---

## 13 · Branch 規則

命名直接對齊資料夾的三態邏輯（explore／analyses／systems／ml），看到分支名稱就知道這是哪一種案件、審查標準該多嚴。

| 前綴 | 對應案件類型 | 範例 | 是否需要 PR |
|---|---|---|---|
| `explore/YYYYMM_[主題]` | Explore 型 | `explore/202607_tcu_control_pdm` | 不需要，可隨時砍掉重練 |
| `analyses/YYYYMM_[主題]` | Analyses 型 | `analyses/202608_deviation_review` | 需要，審查重點是 AR 報告本身 |
| `feat/sys-N-[功能]` | Systems 型（新功能） | `feat/sys-1-monitoring` | 需要，CI 綠燈 + 自我 review |
| `fix/[主題]` | 任何類型的錯誤修正 | `fix/pipeline-date-parsing` | 需要 |
| `ml/[model]-[實驗代號]` | ML 型 | `ml/rul-predictor-exp03` | 進 training/ 前需要，experiments/ 階段不需要 |

> **現有的 `pipeline` 分支是技術債**
> 目前 repo 裡的 `pipeline` 分支沒有範圍、沒有前綴，是命名規則定案前留下的——不需要現在回頭改名，但之後再開 pipeline 相關分支請照 `fix/pipeline-[主題]` 或 `feat/pipeline-[主題]` 命名，不要延續沒有範圍的舊模式。

### main 分支保護

- 不直接 `push` 到 `main`——即使目前一人團隊，一律開分支再合併，養成習慣比之後補規則容易
- `.github/workflows/ci.yml` 要綠燈才能合併
- ★ Zone（`core/`、`schema.py`、`infra/migrations/`、`docs/adr/`）合併前自己重讀一次完整 diff，不因為是自己寫的就跳過
- 🤖 Zone（`frontend/`）UAT 測試通過即可合併，不需要額外卡關拖慢速度

### 合併策略與版本標記

建議 squash merge 進 `main`，讓每個合併進主線的 commit 對應一個完整、可追溯的變更單位，方便之後串到 `change_control/` 底下對應的 CR 紀錄。**但合併之後就不再對這個 commit 做任何竄改**。系統驗證通過、實際部署上線的版本，額外打一個 tag（例如 `v1.0.0-sys1`），讓 git 上的版本號跟部署/驗證紀錄對得上號，稽核時可以直接指到那一個 commit。
