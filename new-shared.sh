#!/usr/bin/env bash
#
# 建立一個新的 shared/<name> 基本骨架（純函式共用邏輯，
# 供 conda pharma-ds 與 systems/SYS-N 以 develop=true 引用）。
# 用法: ./new-shared.sh monitor
#
# 建立完後執行 ./setup.sh 安裝 Poetry 環境（目前 setup.sh 只會自動偵測/安裝
# shared/monitor，新建立的其他 shared 套件要自行在 setup.sh 補上對應步驟，
# 或先手動 cd 進去跑 poetry install）。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log()  { printf '\n\033[1;36m▶ %s\033[0m\n' "$1"; }
ok()   { printf '\033[1;32m✔ %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m⚠ %s\033[0m\n' "$1"; }
die()  { printf '\033[1;31m✘ %s\033[0m\n' "$1" >&2; exit 1; }

if [ $# -ne 1 ]; then
  die "用法: ./new-shared.sh <名稱>，例如 ./new-shared.sh monitor"
fi

NAME="$1"
SHARED_DIR="shared/$NAME"

[[ "$NAME" =~ ^[a-z][a-z0-9_]*$ ]] || die "名稱必須是合法的 Python package 名稱（小寫字母開頭，只能有小寫字母/數字/底線），收到 \"$NAME\""
[ -e "$SHARED_DIR" ] && die "$SHARED_DIR 已存在，中止（避免覆蓋既有內容）"

PKG_NAME="pharma-$(echo "$NAME" | tr '_' '-')"

log "建立 $SHARED_DIR 骨架"

mkdir -p "$SHARED_DIR/$NAME" "$SHARED_DIR/test"

touch "$SHARED_DIR/$NAME/__init__.py"

cat > "$SHARED_DIR/pyproject.toml" <<EOF
[tool.poetry]
name = "$PKG_NAME"
version = "0.1.0"
description = "$NAME"
authors = []
packages = [{ include = "$NAME" }]

[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

cat > "$SHARED_DIR/test/test_placeholder.py" <<'EOF'
def test_placeholder():
    assert True
EOF

ok "$SHARED_DIR 骨架建立完成"

cat <<EOF

下一步:
  1. 到 $SHARED_DIR/pyproject.toml 補上實際需要的依賴（例如 pandas/scipy/statsmodels）
  2. cd $SHARED_DIR && poetry install && poetry run pytest
  3. 若要給 conda pharma-ds／systems/SYS-N 用 develop=true 引用，記得在對應 pyproject.toml 加上：
       $PKG_NAME = { path = "../../$SHARED_DIR", develop = true }

EOF
