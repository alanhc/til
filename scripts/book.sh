generate_links() {
    local dir="$1"
    local level="$2"
    local output_file="$3"
    
    local has_files=false
    for file in "$dir"/*; do
        # local filename=$(basename "$file")
        if [ -d "$file" ]; then
            local filename=$(basename "$file")
            local name="${filename%.*}"
            echo "# $name" >> "$output_file"
            
            for f in "$file"/*; do
                local filename=$(basename "$f")
                local name="${filename%.*}"
                #local file_out="$(printf '  %.0s' $(seq 0 $level))- [$name]($f)"
                formatted_path=$(echo "$f" | sed -E 's|^\./src/||; s|//|/|g')
                local file_out="- [$name]($formatted_path)"
                echo "$file_out" >> "$output_file"
                # echo "- [$name]($link)"
                # echo "- [$name]()"
            done
       
        elif [ -f "$file" ]; then
            
            local filename=$(basename "$file")
            local name="${filename%.*}"
            #local file_out="$(printf '  %.0s' $(seq 0 $level))- [$name]($f)"
            formatted_path=$(echo "$file" | sed -E 's|^\./src/||; s|//|/|g')
            local file_out="- [$name]($formatted_path)"
            echo "$file_out" >> "$output_file"
        fi
    done

}