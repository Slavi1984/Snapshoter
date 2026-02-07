#!/usr/bin/env python3
import requests
import json
import os 
import time


port_rtsp = 8554
nazwy_rtsp = []
streamy_rtsp = []



# Ustalennie adresów wszystkich streamów rtsp

api_konfiguracja = requests.get('http://localhost:9997/v3/config/global/get').json()
port_rtsp = api_konfiguracja["rtspAddress"]


api_streamy = requests.get('http://localhost:9997/v3/paths/list').json()


for i in api_streamy['items']:
    if i["source"]['type'] == 'rtspSession':
        nazwy_rtsp.append(i['name'])

print(nazwy_rtsp)


for i in nazwy_rtsp:
    streamy_rtsp.append(f'rtsp://localhost{port_rtsp}/'+i)

print(streamy_rtsp)


# Ustalenie głównej ścieżki zapisu

snapdir = os.getcwd()+'/snapshots'
os.chdir(snapdir)

# Nagrywanie streamów

# os.system('ffmpeg -hide_banner -y -loglevel error -rtsp_transport tcp -use_wallclock_as_timestamps 1 -i rtsp://localhost:8554/a -vcodec copy -acodec copy -f segment -reset_timestamps 1 -segment_time 900 -segment_format mkv -segment_atclocktime 1 -strftime 1 test.mkv')

# pętla snapshotowa

for i in range(5):
    time.sleep(1)
    os.system(f'ffmpeg -skip_frame nokey -y -i {streamy_rtsp[0]} -vframes 1 test{i}.jpg')



#
#ffmpeg -re -i vid1.mp4 -f rtsp -rtsp_transport tcp  rtsp://localhost:8554/a
#mediamtx
#r