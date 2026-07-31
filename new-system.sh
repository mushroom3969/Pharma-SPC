#!/usr/bin/env bash
#
# 建立一個新的 systems/SYS-N 基本骨架（對照手冊 07 節 Systems 型結構）。
# 用法: ./new-system.sh SYS-2-BatchRelease
#
# 建立完後執行 ./setup.sh，[3/5] 會自動偵測到新的 pyproject.toml 並裝好 Poetry 環境。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log()  { printf '\n\033[1;36m▶ %s\033[0m\n' "$1"; }
ok()   { printf '\033[1;32m✔ %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m⚠ %s\033[0m\n' "$1"; }
die()  { printf '\033[1;31m✘ %s\033[0m\n' "$1" >&2; exit 1; }

if [ $# -ne 1 ]; then
  die "用法: ./new-system.sh <SYS-N-名稱>，例如 ./new-system.sh SYS-2-BatchRelease"
fi

SYS_NAME="$1"
SYS_DIR="systems/$SYS_NAME"

[[ "$SYS_NAME" == SYS-* ]] || warn "名稱通常以 SYS- 開頭（例如 SYS-2-BatchRelease），目前是 \"$SYS_NAME\"，仍會繼續建立"
[ -e "$SYS_DIR" ] && die "$SYS_DIR 已存在，中止（避免覆蓋既有內容）"

# Poetry 套件名稱只接受小寫字母、數字、連字號
PKG_NAME="$(echo "$SYS_NAME" | tr '[:upper:]' '[:lower:]')"

log "建立 $SYS_DIR 骨架"

mkdir -p "$SYS_DIR"/src/core "$SYS_DIR"/src/orchestration "$SYS_DIR"/src/frontend "$SYS_DIR"/tests/uat

cat > "$SYS_DIR/pyproject.toml" <<EOF
[tool.poetry]
name = "$PKG_NAME"
version = "0.1.0"
description = "$SYS_NAME"
authors = []
package-mode = false

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115"
uvicorn = { extras = ["standard"], version = "^0.32" }
pydantic = "^2.9"
pharma-core = { path = "../../shared/pharma_core", develop = true }

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
httpx = "^0.27"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

touch "$SYS_DIR/src/__init__.py"
touch "$SYS_DIR/src/core/__init__.py"
touch "$SYS_DIR/src/orchestration/__init__.py"
touch "$SYS_DIR/src/frontend/.gitkeep"
touch "$SYS_DIR/tests/__init__.py"
touch "$SYS_DIR/tests/uat/.gitkeep"

cat > "$SYS_DIR/tests/test_placeholder.py" <<'EOF'
def test_placeholder():
    assert True
EOF

cat > "$SYS_DIR/src/schema.py" <<'EOF'
from pydantic import BaseModel
EOF

: > "$SYS_DIR/src/service.py"

cat > "$SYS_DIR/src/router.py" <<'EOF'
from fastapi import APIRouter

router = APIRouter()
EOF

cat > "$SYS_DIR/src/main.py" <<EOF
from fastapi import FastAPI

from src.router import router

app = FastAPI(title="$SYS_NAME")
app.include_router(router)
EOF

ok "$SYS_DIR 骨架建立完成"

cat <<EOF

下一步:
  1. ./setup.sh                 # 讓 [3/5] 幫 $SYS_NAME 裝 Poetry 環境
  2. cd $SYS_DIR && poetry run uvicorn src.main:app --reload

EOF
