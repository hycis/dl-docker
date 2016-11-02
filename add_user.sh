#!/usr/bin/env bash

sudo adduser $1
sudo gpasswd -a $1 docker
sudo gpasswd -a $1 nvidia-docker

# personal data dir
sudo mkdir -p /raid/$1
sudo chown -R $1:docker /raid/$1/

# personal notebook dir
sudo mkdir -p /raid/notebooks/$1
sudo chown -R $1:docker /raid/notebooks/$1/
