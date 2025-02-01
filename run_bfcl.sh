#!/bin/bash

set -e
echo "---------------"
echo "Compiling..."
echo "---------------"
python3 bfcolang.py programs/"$1".bfcl "$2"
echo "---------------"
echo "Running..."
echo "---------------"
if [ -n "$2" ];
then
	./bfinterpreter generated/"$1".bf "$2"
else
	./bfinterpreter generated/"$1".bf
fi
