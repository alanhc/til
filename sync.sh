#!/bin/bash

set -a
[ -f .env ] && . .env
set +a 

rm -rf posts
mkdir posts
cp -r "$POSTS_PATH"/ posts/


# count files in each folder
for folder in posts/*; do
    if [ -d "$folder" ]; then
        num_files=$(find "$folder" -type f | wc -l)
        echo "$folder: $num_files"
    fi
done

if command -v tree &> /dev/null; then
    tree posts
else
    echo "tree command not found. Please install it to see the directory structure."
fi
 
