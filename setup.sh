#!/bin/bash
sudo apt-get update
sudo apt-get install -y graphviz libgraphviz-dev
python -m pip install --upgrade pip
pip install -r requirements.txt
