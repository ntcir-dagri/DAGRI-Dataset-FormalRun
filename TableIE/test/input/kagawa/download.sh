URL_FILE=urls.txt

if command -v wget >/dev/null 2>&1; then
  for URL in $(cat ${URL_FILE}); do
    wget "${URL}"
  done
else
  echo "wgetコマンドが必要になります"
fi
