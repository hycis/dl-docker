#!/bin/sh

for i in `seq 0 7`;
do
    echo "GPU $i"
    NV_GPU="$i" nvidia-docker run -d -it --name gpu$i -p 888$i:8888 -p 600$i:6006 -v /raid:/raid sap-icn/dl-docker bash
done

nvidia-docker run -d -it --name gpus -p 8888:8888 -p 6008:6006 -v /raid:/raid sap-icn/dl-docker bash
