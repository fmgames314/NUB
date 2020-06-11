#!/bin/bash

while true
do
raspivid -t 0 -w 640 -h 480 -hf -vf -ih -fps 15 -o - | nc 192.168.1.200 7001
sleep 10
done

#with audio
#raspivid -t 0 -w 640 -h 480 -hf -vf -ih -fps 15 -o - | ffmpeg -i - -f alsa -ac 1 -i hw:1,0 -map 0:0 -map 1:0 -vcodec copy -acodec aac -strict -2 -f flv pipe:1 | nc wtfip.frankmagazu.com 7001
