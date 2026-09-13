# 讀 `git diff --unified=0` 的輸出，對「新增的行」比對關鍵字。
# 用法：awk -v PATF=patterns -v ALLOWF=allowlist -f scan.awk diff.txt
# 輸出：檔案:行號: 內容        （有輸出就代表命中）
BEGIN {
  np = 0; na = 0
  while ((getline line < PATF) > 0) {
    if (line ~ /^[ \t]*$/ || line ~ /^[ \t]*#/) continue
    pat[++np] = tolower(line)
  }
  while ((getline line < ALLOWF) > 0) {
    if (line ~ /^[ \t]*$/ || line ~ /^[ \t]*#/) continue
    allow[++na] = line
  }
}

# 檔名（要放在 /^\+/ 之前，因為 +++ 也是 + 開頭）
/^\+\+\+ / { file = substr($0, 5); sub(/^b\//, "", file); next }
/^--- /    { next }

# hunk header: @@ -a,b +c,d @@  取 c 當新檔的起始行號
/^@@ / {
  if (match($0, /\+[0-9]+/)) ln = substr($0, RSTART + 1, RLENGTH - 1) + 0
  next
}

/^\+/ {
  content = substr($0, 2)
  loc = file ":" ln
  low = tolower(content)
  for (i = 1; i <= np; i++) {
    if (low ~ pat[i]) {
      skip = 0
      for (j = 1; j <= na; j++) if ((loc ": " content) ~ allow[j]) { skip = 1; break }
      if (!skip) print loc ": " content
      break
    }
  }
  ln++
}
