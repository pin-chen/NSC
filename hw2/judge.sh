#!/bin/bash

for (( ; ; ))
do 
	echo TEST
	python3 generate_cmd.py > cmd.txt && python3 109550206.py < cmd.txt > 1.txt && python3 109550129.py < cmd.txt > 2.txt && python3 109550004.py < cmd.txt > 3.txt && colordiff 1.txt 2.txt && colordiff 2.txt 3.txt
	if [ $? -ne 0 ] 
	then
		break
	fi	
done
