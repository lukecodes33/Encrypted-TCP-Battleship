#!/bin/bash
echo "Input port number to connect to: "
read port

python3 client.py localhost "$port"