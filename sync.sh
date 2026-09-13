#!/bin/bash

set -a
[ -f .env ] && . .env
set +a 





# if command -v tree &> /dev/null; then
#     tree posts
# else
#     echo "tree command not found. Please install it to see the directory structure."
# fi

source scripts/book.sh

# 定义要遍历的目录
TARGET_DIR="./src/posts"  # 可根据需要修改为目标目录
OUTPUT_FILE="src/SUMMARY.md"
# remove if exists
if [ -d "$TARGET_DIR" ]; then
    rm -r $TARGET_DIR
fi

cp -r "$POSTS_PATH"/ src/posts/
echo "# title" > "$OUTPUT_FILE"
echo " # 1" >> "$OUTPUT_FILE"
# 创建或清空 summary.md 文件
# echo -e "[Introduction](README.md)\n" > "$OUTPUT_FILE"
# 开始生成链接
generate_links $TARGET_DIR 0 $OUTPUT_FILE

echo "summary.md has been generated."

# count files in each folder
for folder in posts/*; do
    if [ -d "$folder" ]; then
        num_files=$(find "$folder" -type f | wc -l)
        echo "$folder: $num_files"
    fi
done