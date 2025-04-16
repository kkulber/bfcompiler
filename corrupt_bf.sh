#!/bin/bash

echo "------------------------------------"
echo "Corrupting $1..."
echo "------------------------------------"

content=$(<"$1")
length=${#content}
remove_index=$(( RANDOM % length ))
corrupted="${content:0:remove_index}${content:remove_index+1}"
echo -n "$corrupted" > "$1"