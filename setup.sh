#!/bin/bash
sudo apt-get update
sudo apt-get install -y graphviz libgraphviz-dev
pip install --force-reinstall -r requirements.txt
