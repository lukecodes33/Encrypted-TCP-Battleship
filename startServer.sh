#!/bin/bash
echo "Input port number to host server on: "
read port

python3 battleshipServer.py "$port"
