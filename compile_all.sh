#!/bin/bash

for file in programs/*; do
    echo "-------------------"
    echo "Compiling $file..."
    python3 bfcolang.py "$file"
done
echo "-------------------"
