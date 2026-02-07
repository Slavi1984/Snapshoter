#!/usr/bin/env python3
import requests
import json
import os 
import time
import threading
from datetime import date, datetime


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

#print(nazwy_rtsp)


for i in nazwy_rtsp:
    streamy_rtsp.append(f'rtsp://localhost{port_rtsp}/'+i)

#print(streamy_rtsp)


# Ustawienia i interfejs



# Ustalenie głównej ścieżki zapisu

snapdir = os.getcwd()+'/snapshots'

os.chdir(snapdir)
if not os.path.exists(snapdir):
    os.makedirs(snapdir)


dir_date = str(date.today())
if not os.path.exists(dir_date):
    os.makedirs(dir_date)
os.chdir(dir_date)


dir_time = str(datetime.now()).split()[1]
dir_time = dir_time[:len(dir_time)-7]
if not os.path.exists(dir_time):
    os.makedirs(dir_time)
os.chdir(dir_time)



# Nagrywanie streamów

# os.system('ffmpeg -hide_banner -y -loglevel error -rtsp_transport tcp -use_wallclock_as_timestamps 1 -i rtsp://localhost:8554/a -vcodec copy -acodec copy -f segment -reset_timestamps 1 -segment_time 900 -segment_format mkv -segment_atclocktime 1 -strftime 1 test.mkv')



# pętla snapshotowa

frame_period = 1

def snaphot_loop(kamera,frame_period):

    if not os.path.exists(kamera):
        os.makedirs(kamera)
    x = 0
    while(x<5):
        time.sleep(frame_period-1)
        file_name = str(datetime.now()).split()[1].replace('.','-').replace(':','-')+'.jpg'
        os.system(f'ffmpeg -skip_frame nokey -y -i rtsp://localhost{port_rtsp}/{kamera} -vframes 1 {file_name}')
        os.system(f'mv {file_name} {kamera}/{file_name}')
        x += 1




# Uruchomienie równoczesnego zapisu z wielu kamer

daemony_kamerowe = {}
for i in nazwy_rtsp:
    daemony_kamerowe[i] = threading.Thread(target=snaphot_loop,args=(i,1))
    daemony_kamerowe[i].setDaemon(True)  

for i in daemony_kamerowe:
    daemony_kamerowe[i].start()


print(daemony_kamerowe)

time.sleep(10)


#
#ffmpeg -re -i vid1.mp4 -f rtsp -rtsp_transport tcp  rtsp://localhost:8554/a
#mediamtx
#r.replace('.','-')