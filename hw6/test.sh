#!/usr/bin/sh
`echo "colordiff static/file_02.txt  target/file_02.txt" | tr '[1-9]' "$1"` && echo Correct || echo Incorrect