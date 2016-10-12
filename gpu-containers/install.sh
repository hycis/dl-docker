#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo -E pip install -r "${DIR}/requirements.txt"
sudo cp $DIR/gpu-containers /usr/bin/
sudo cp $DIR/gpu-containers.py /usr/bin/
sudo chmod 777 /usr/bin/gpu-containers
sudo chmod 777 /usr/bin/gpu-containers.py
echo "Done."