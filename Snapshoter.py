#!/usr/bin/env python3
import requests
import json
import os 
import time


# Ustalennie adresów wszystkich streamów rtsp
api_streamy = requests.get('http://localhost:9997/v3/paths/list')
print(api_streamy.json())

api_konfiguracja = requests.get('http://localhost:9997/v3/config/global/get')
print(api_konfiguracja.json())

port_rtsp = 0
streamy_rtsp = ['rtsp://localhost:8554/a','']


# Ustalenie głównej ścieżki zapisu
snapdir = os.getcwd()+'/snapshots'
os.chdir(snapdir)


# pętla snapshotowa
for i in range(5):
    time.sleep(1)
    os.system(f'ffmpeg -skip_frame nokey -y -i {streamy_rtsp[0]} -vframes 1 test{i}.jpg')



#
#ffmpeg -re -i vid1.mp4 -f rtsp -rtsp_transport tcp  rtsp://localhost:8554/a
#mediamtx
#