{ 
  # Print CSV header
  echo "device_type,grid_template_area";

  # Find all .css files and process them
  find . -type f -name '*.css' -print0 | while IFS= read -r -d '' file; do
    
    # Strip off the ".css" extension for device_type
    device_type=$(basename "$file" .css)
    
    # Use sed to:
    #   1) read entire file into pattern space  (:a;N;$!ba)
    #   2) remove multiline comments           s@/\*.*?\*/@@g
    #   3) remove tabs, carriage returns       s/\t//g; s/\r//g
    #   4) replace newlines with a single space
    #   5) replace any sequence of 2+ spaces with a single space
    grid_template_area=$(
      sed -E ':a;N;$!ba; 
              s@/\*.*?\*/@@g; 
              s/\t//g; 
              s/\r//g; 
              s/\n/ /g; 
              s/ {2,}/ /g;' "$file"
    )
    
    # Print CSV row as: device_type,"grid_template_area"
    echo "$device_type,\"$grid_template_area\""
    
  done;

} > output.csv
