#!/bin/bash

stdbuf -oL ./bfinterpreter "$1" | while IFS= read -r line;
do
	eval "$line"
done 
