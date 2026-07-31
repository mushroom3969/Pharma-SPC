#!/usr/bin/env bash
#
# pharma-analytics 一鍵環境建置腳本
# 用法: 從 repo 根目錄執行 ./setup.sh
#
# 依「PHARMA-ANALYTICS 專案流程手冊」02 節的順序執行：
#   1. shared/pharma_core   (Poetry)  — 其他環境都靠 editable install 引用它，必須最先裝
#   2. conda 環境 pharma-ds           — explore/ analyses/ ml/ 共用，含 Jupyter kernel
#   3. systems/SYS-N         (Poetry, in-project venv)  — 逐一偵測已存在的系統
#   4. pipeline               (Poetry, in-project venv, dbt)
#   5. frontend               (npm/pnpm) — 有 package.json 才裝，自動偵測並跳過
#
# 腳本本身是冪等的：資料夾與設定檔只在不存在時才建立，重複執行不會覆蓋既有工作內容。

set -uo pipefail
shopt -s nullglob

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

FAILED=()

log()  { printf '\n\033[1;36m▶ %s\033[0m\n' "$1"; }
ok()   { printf '\033[1;32m✔ %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m⚠ %s\033[0m\n' "$1"; }
fail() { printf '\033[1;31m✘ %s\033[0m\n' "$1"; FAILED+=("$1"); }
has()  { command -v "$1" >/dev/null 2>&1; }

# 已知環境坑：shell 裡殘留的 VIRTUAL_ENV / CONDA_PREFIX 會讓 poetry run 悄悄用錯 Python
unset VIRTUAL_ENV CONDA_PREFIX

# ============================================================
# 0. 建立資料夾骨架
# ============================================================
log "建立資料夾骨架"

mkdir -p shared/pharma_core/pharma_core
mkdir -p shared/pharma_core/tests
mkdir -p explore analyses systems
mkdir -p pipeline/models/staging pipeline/models/intermediate pipeline/models/mart
mkdir -p pipeline/seeds pipeline/tests/singular pipeline/scripts
mkdir -p infra/migrations/versions
mkdir -p ml/features ml/experiments ml/training ml/evaluation ml/model_cards
mkdir -p monitoring/drift
mkdir -p docs/adr
mkdir -p .github/workflows

# 讓 git 能追蹤目前還是空的資料夾
for d in explore analyses systems ml/features ml/experiments ml/training ml/evaluation ml/model_cards monitoring/drift docs/adr; do
  [ -f "$d/.gitkeep" ] || touch "$d/.gitkeep"
done

ok "資料夾骨架就緒"

# ============================================================
# 0.5 git init（冪等，已是 git repo 時安全略過）
# ============================================================
if has git; then
  if [ -d .git ]; then
    log "已是 git repository，略過 git init"
  else
    log "初始化 git repository"
    git init && ok "git init 完成" || fail "git init 失敗"
  fi
else
  warn "找不到 git，略過 git init"
fi

# ============================================================
# 1. 建立預設設定檔（只在不存在時建立，不覆蓋既有內容）
# ============================================================
log "建立預設設定檔"

if [ ! -f shared/pharma_core/pyproject.toml ]; then
  cat > shared/pharma_core/pyproject.toml <<'EOF'
[tool.poetry]
name = "pharma-core"
version = "0.1.0"
description = "Shared core library for pharma-analytics"
authors = []
packages = [{ include = "pharma_core" }]

[tool.poetry.dependencies]
python = "^3.11"
alembic = "^1.13"
sqlalchemy = "^2.0"
psycopg2-binary = "^2.9"
python-dotenv = "^1.0"
pandas = "^2.2"
scipy = "^1.13"
statsmodels = "^0.14"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
  [ -f shared/pharma_core/pharma_core/__init__.py ] || touch shared/pharma_core/pharma_core/__init__.py
fi

if [ ! -f shared/pharma_core/tests/test_placeholder.py ]; then
  cat > shared/pharma_core/tests/test_placeholder.py <<'EOF'
def test_placeholder():
    assert True
EOF
fi

# Alembic（DB schema 基線，07 節 PHASE 0）— 用 shared/pharma_core 的 Poetry 環境執行：
#   cd shared/pharma_core && poetry run alembic -c ../../infra/alembic.ini upgrade head
if [ ! -f infra/alembic.ini ]; then
  cat > infra/alembic.ini <<'EOF'
[alembic]
script_location = %(here)s/migrations
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
fi

if [ ! -f infra/migrations/env.py ]; then
  cat > infra/migrations/env.py <<'EOF'
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

config = context.config

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL not set -- copy infra/.env.example to .env at repo root and fill it in"
    )
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF
fi

if [ ! -f infra/migrations/script.py.mako ]; then
  cat > infra/migrations/script.py.mako <<'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOF
fi

[ -f infra/migrations/versions/.gitkeep ] || touch infra/migrations/versions/.gitkeep

if [ ! -f pipeline/pyproject.toml ]; then
  cat > pipeline/pyproject.toml <<'EOF'
[tool.poetry]
name = "pharma-pipeline"
version = "0.1.0"
description = "dbt pipeline for pharma-analytics"
authors = []
package-mode = false

[tool.poetry.dependencies]
python = "^3.11"
dbt-core = "^1.8"
dbt-postgres = "^1.8"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
fi

if [ ! -f pipeline/dbt_project.yml ]; then
  cat > pipeline/dbt_project.yml <<'EOF'
name: 'pharma_pipeline'
version: '1.0.0'
config-version: 2

profile: 'pharma_pipeline'

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]

models:
  pharma_pipeline:
    staging:
      +materialized: view
    intermediate:
      +materialized: view
    mart:
      +materialized: table
EOF
fi

if [ ! -f environment.yml ]; then
  cat > environment.yml <<'EOF'
name: pharma-ds
channels:
  - conda-forge
dependencies:
  - python=3.11
  - pandas
  - numpy
  - matplotlib
  - jupyterlab
  - ipykernel
  - nbstripout
  - pip
EOF
fi

if [ ! -f infra/.env.example ]; then
  cat > infra/.env.example <<'EOF'
DATABASE_URL=postgresql://user:password@localhost:5432/pharma_analytics
EOF
fi

if [ ! -f .gitattributes ]; then
  cat > .gitattributes <<'EOF'
*.ipynb filter=nbstripout
EOF
fi

if [ ! -f .gitignore ]; then
  cat > .gitignore <<'EOF'
.env
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
dbt_packages/
target/
logs/
profiles.yml
node_modules/
EOF
fi

if [ ! -f .github/workflows/ci.yml ]; then
  cat > .github/workflows/ci.yml <<'EOF'
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install poetry
      - run: cd shared/pharma_core && poetry install && poetry run pytest
EOF
fi

ok "預設設定檔就緒"

# ============================================================
# 2. [1/5] Poetry: shared/pharma_core
# ============================================================
log "[1/5] 安裝 shared/pharma_core (Poetry)"
if has poetry; then
  if (cd shared/pharma_core && unset VIRTUAL_ENV CONDA_PREFIX && poetry install); then
    ok "pharma_core 安裝完成"
  else
    fail "pharma_core 安裝失敗"
  fi
else
  warn "找不到 poetry，跳過 pharma_core 安裝（請先安裝：https://python-poetry.org）"
fi

# ============================================================
# 3. [2/5] Conda: pharma-ds（explore/ analyses/ ml/ 共用，含 Jupyter kernel）
# ============================================================
log "[2/5] 建立 / 更新 conda 環境 pharma-ds"
if has conda; then
  if conda env list | grep -q "^pharma-ds "; then
    conda env update -n pharma-ds -f environment.yml --prune
  else
    conda env create -n pharma-ds -f environment.yml
  fi

  if [ $? -eq 0 ]; then
    # 把 pharma_core 以 editable 模式裝進 pharma-ds，確保用到最新原始碼
    conda run -n pharma-ds pip install -e shared/pharma_core \
      && conda run -n pharma-ds python -m ipykernel install --user --name pharma-ds --display-name "pharma-ds" \
      && ok "conda 環境 pharma-ds 就緒" \
      || fail "pharma-ds 環境裝好了，但 editable install 或 kernel 註冊失敗"
  else
    fail "conda 環境 pharma-ds 建立/更新失敗"
  fi
else
  warn "找不到 conda，跳過 pharma-ds 環境建立（請先安裝 Miniconda/Anaconda）"
fi

if has conda && [ -d .git ]; then
  if conda run -n pharma-ds nbstripout --install; then
    ok "nbstripout 已註冊（*.ipynb 的執行輸出會在 commit 時自動清除）"
  else
    fail "nbstripout --install 失敗"
  fi
elif [ ! -d .git ]; then
  warn "尚未是 git repository，略過 nbstripout 註冊"
fi

# ============================================================
# 4. [3/5] Poetry: systems/SYS-N（in-project venv）— 逐一偵測已存在的系統
# ============================================================
log "[3/5] 安裝 systems/SYS-N (Poetry, in-project venv)"
sys_dirs=(systems/*/)
if [ ${#sys_dirs[@]} -eq 0 ]; then
  warn "尚未建立任何 systems/SYS-N，略過（案件分流判斷確定要走 Systems 型後，用 poetry new 或手動建立 pyproject.toml 即可）"
elif ! has poetry; then
  warn "找不到 poetry，跳過 systems 安裝"
else
  for dir in "${sys_dirs[@]}"; do
    if [ -f "${dir}pyproject.toml" ]; then
      log "  → ${dir}"
      if (cd "$dir" && unset VIRTUAL_ENV CONDA_PREFIX && poetry config virtualenvs.in-project true --local && poetry install); then
        ok "${dir} 安裝完成"
      else
        fail "${dir} 安裝失敗"
      fi
    fi
  done
fi

# ============================================================
# 5. [4/5] Poetry: pipeline（in-project venv, dbt）
# ============================================================
log "[4/5] 安裝 pipeline (Poetry, in-project venv, dbt)"
if has poetry; then
  if (cd pipeline && unset VIRTUAL_ENV CONDA_PREFIX && poetry config virtualenvs.in-project true --local && poetry install); then
    ok "pipeline 安裝完成"
  else
    fail "pipeline 安裝失敗"
  fi
else
  warn "找不到 poetry，跳過 pipeline 安裝"
fi

# ============================================================
# 6. [5/5] npm/pnpm: frontend（有 package.json 才裝，自動偵測並跳過）
# ============================================================
log "[5/5] 偵測前端（有 package.json 才安裝）"
frontend_found=false
for dir in systems/*/src/frontend; do
  if [ -f "${dir}/package.json" ]; then
    frontend_found=true
    log "  → ${dir}"
    if has pnpm; then
      (cd "$dir" && pnpm install) && ok "${dir} 安裝完成" || fail "${dir} 安裝失敗"
    elif has npm; then
      (cd "$dir" && npm install) && ok "${dir} 安裝完成" || fail "${dir} 安裝失敗"
    else
      warn "找不到 npm/pnpm，跳過 ${dir}"
    fi
  fi
done
if [ "$frontend_found" = false ]; then
  warn "尚未建立任何 frontend/package.json，略過前端安裝（符合手冊現況：前端尚未啟動）"
fi

# ============================================================
# 完成
# ============================================================
log "全部完成"

if [ ${#FAILED[@]} -gt 0 ]; then
  warn "以下步驟失敗，請檢視上方錯誤訊息："
  for f in "${FAILED[@]}"; do printf '  - %s\n' "$f"; done
fi

cat <<'EOF'

下一步：
  1. cp infra/.env.example .env         # 依實際 DB 連線資訊填寫，.env 不進版控
  2. conda activate pharma-ds
  3. cd shared/pharma_core && poetry run alembic -c ../../infra/alembic.ini upgrade head
                                         # DB schema 基線（07 節 PHASE 0），確認能連線
  4. 建立 pipeline/profiles.yml（依 .env 內容手動建立，已在 .gitignore 排除，不進版控）
  5. cd pipeline && poetry run dbt debug   # 確認 dbt 連線設定正確後再 dbt run

（git init 與 nbstripout 註冊已自動處理，不需要手動再跑）

EOF

if [ ${#FAILED[@]} -gt 0 ]; then
  exit 1
fi
