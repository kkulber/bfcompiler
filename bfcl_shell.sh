#!/bin/bash

# Files 
BFCL_FILE="programs/tmp_shell.bfcl"
BF_FILE="generated/tmp_shell.bf"

# Create shell program
> "$BFCL_FILE"

echo "Bfcolang shell started. Enter command or type \"exit\" to quit."

previous_cmd=""

while true; do
    # Command input
    read -p "# " CMD
    
    # Exit
    if [[ "$CMD" == "exit" ]]; then
        echo "Exiting shell."
        rm -f "$BFCL_FILE"
        rm -f "$BF_FILE"
        break
    fi
    
    # Remove last print if it exists
    if [[ -s "$BFCL_FILE" ]]; then
        sed -i '$d' "$BFCL_FILE"
    fi
    
    # Add previous command without print
    if [[ -n "$previous_cmd" ]]; then
        echo "$previous_cmd;" >> "$BFCL_FILE"
    fi
    
    # Print the current command
    echo ".($CMD);" >> "$BFCL_FILE"
    
    # Store previous command
    previous_cmd="$CMD"
    
    # Run
    if ! python3 bfcolang.py "$BFCL_FILE" > /dev/null; then
        sed -i '$d' "$BFCL_FILE"
        sed -i '$d' "$BFCL_FILE"
        continue
    fi
    ./bfinterpreter "$BF_FILE"

done
