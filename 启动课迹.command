#!/bin/zsh
cd -- "${0:A:h}"
if [[ ! -d node_modules ]]; then
  echo '请先在本目录运行 npm ci 安装依赖。'
  exit 1
fi
npm run build || exit 1
exec python3 server/app.py
