#!/bin/bash

for port in 35903 8081 53 4840 40275; do 
	echo "====Port $port ===="
	curl -sI --max-time 5 http://127.0.0.1:$port | head -5
	echo ""
done
