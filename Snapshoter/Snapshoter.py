import requests
import json
import os 
import time
import threading
from datetime import date, datetime
import typer
from pathlib import Path



class CameraRTSP:
    def __init__(self,name,port_rtsp):
        self.name = name
        self.camera_path = f'rtsp://localhost{port_rtsp}/{name}'
        self.snapshot_period = 3.0
        self.snapshot_active = True
        self.film_active = False



def getRtspPort():
    api_konfiguracja = requests.get('http://localhost:9997/v3/config/global/get').json()
    port_rtsp = api_konfiguracja["rtspAddress"]
    return port_rtsp



def getRtspStreams():
    nazwy_rtsp = []
    api_streamy = requests.get('http://localhost:9997/v3/paths/list').json()
    for i in api_streamy['items']:
        if i["source"]['type'] == 'rtspSession':
            nazwy_rtsp.append(i['name'])
    return nazwy_rtsp



def createRtspCameras(streams,port,camera_class):
    all_cameras = {}
    for i in streams:
        all_cameras[i] = camera_class(i,port)
    return all_cameras


#settings = {'abc':[False,5]}

def setCameraSnapshotMode(cameras,snaphsot_settings):
    for cam in cameras:
        cameras[cam].snapshot_active = snaphsot_settings[cam][0]
        cameras[cam].snapshot_period = snaphsot_settings[cam][1]



def setCameraFilmMode(cameras,camera_settings):
    for cam in cameras:
        cameras[cam].film_active = camera_settings[cam]



# Ustalenie głównej ścieżki zapisu
def changeToSaveDirectory(snapshots_goto_dir):
    snapshots_goto_dir = snapshots_goto_dir+'/snapshots'

    if not os.path.exists(snapshots_goto_dir):
        os.makedirs(snapshots_goto_dir)
    os.chdir(snapshots_goto_dir)

    dir_date = str(date.today())
    if not os.path.exists(dir_date):
        os.makedirs(dir_date)
    os.chdir(dir_date)

    dir_time = str(datetime.now()).split()[1]
    dir_time = dir_time[:len(dir_time)-7]
    if not os.path.exists(dir_time):
        os.makedirs(dir_time)
    os.chdir(dir_time)




## Nagrywanie streamów
#
## os.system('ffmpeg -hide_banner -y -loglevel error -rtsp_transport tcp -use_wallclock_as_timestamps 1 -i rtsp://localhost:8554/a -vcodec copy -acodec copy -f segment -reset_timestamps 1 -segment_time 900 -segment_format mkv -segment_atclocktime 1 -strftime 1 test.mkv')

def makeASnapshot(kamera):
    file_name = str(datetime.now()).split()[1].replace('.','-').replace(':','-')+'.jpg'
    os.system(f'ffmpeg -skip_frame nokey -y -i {kamera.camera_path} -vframes 1 -loglevel panic {kamera.name}/{file_name} &')
    print(os.getcwd()+'/'+file_name)


def snaphot_loop(kamera):
    if not os.path.exists(kamera.name):
        os.makedirs(kamera.name)
    while(True):
        time.sleep(kamera.snapshot_period)
        makeASnapshot(kamera)



# Uruchomienie równoczesnego zapisu z wielu kamer
def runSnapshotThreads(cameras,func):
    daemony_kamerowe = {}
    for i in cameras:
        daemony_kamerowe[i] = threading.Thread(target=func,args=([cameras[i]]))
        daemony_kamerowe[i].setDaemon(True)  
    for i in daemony_kamerowe:
        daemony_kamerowe[i].start()



def main():
    changeToSaveDirectory(os.getcwd())
    all_cameras = createRtspCameras(getRtspStreams(),getRtspPort(),CameraRTSP)
    runSnapshotThreads(all_cameras,snaphot_loop)
    time.sleep(30)



if __name__=='__main__':
    main()
