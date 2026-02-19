import requests
import json
import os 
import time
import threading
from datetime import date, datetime
import typer
from pathlib import Path
import csv
from rich import print
from rich.console import Console
from rich.table import Table
from typing import Annotated

class CameraRTSP:
    def __init__(self,name,port_rtsp):
        self.name = name
        self.camera_path = f'rtsp://localhost{port_rtsp}/{name}'
        self.snapshot_active = True
        self.snapshot_period = 5.0
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




def makeASnapshot(kamera):
    file_name = str(datetime.now()).split()[1].replace('.','-').replace(':','-')+'.jpg'
    os.system(f'ffmpeg -skip_frame nokey -y -i {kamera.camera_path} -vframes 1 -loglevel panic {kamera.name}/{file_name} &')
    print(os.getcwd()+'/'+file_name)



def snapshotLoop(kamera):
    if kamera.snapshot_active:
        if not os.path.exists(kamera.name):
            os.makedirs(kamera.name)
        while(True):
            makeASnapshot(kamera)
            time.sleep(kamera.snapshot_period)



def cameraLoop(kamera):
    print(kamera.film_active)
    if kamera.film_active==True:
        print('wtf')
        if not os.path.exists(kamera.name):
            os.makedirs(kamera.name)
        os.system(f'ffmpeg -hide_banner -y -loglevel error -rtsp_transport tcp -use_wallclock_as_timestamps 1 -i {kamera.camera_path} -vcodec copy -acodec copy -f segment -reset_timestamps 1 -segment_time 900 -segment_format mkv -segment_atclocktime 1 -strftime 1 {kamera.name}/%Y%m%dT%H%M%S.mkv')
    


# Uruchomienie równoczesnego zapisu z wielu kamer
def runSnapshotThreads(cameras,func):
    daemony_kamerowe = {}
    for i in cameras:
        daemony_kamerowe[i] = threading.Thread(target=func,args=([cameras[i]]))
        daemony_kamerowe[i].setDaemon(True)  
    for i in daemony_kamerowe:
        daemony_kamerowe[i].start()


def readSetting(csv_path):
    csv_dict = {}
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
            csv_dict[line[0]] = {
            'snapshot_active':line[1],
            'snapshot_period':float(line[2]),
            'film_active':line[3]}  
    return csv_dict


def setCameraSettings(cameras,csv_settings):
    for i in cameras:
        if i in csv_settings:
            cameras[i].snapshot_active = csv_settings[i]['snapshot_active']
            cameras[i].snapshot_period = csv_settings[i]['snapshot_period']
            cameras[i].film_active = csv_settings[i]['film_active']


def writeSettingsTocsv(kameras,csv_settings,csv_path):
    with open(csv_path, 'w') as csv_file:
        for i in kameras:
            csv_writer = csv.writer(csv_file)
            if i in csv_settings:
                line = [i,csv_settings[i]['snapshot_active'],csv_settings[i]['snapshot_period'],csv_settings[i]['film_active']]
                csv_writer.writerow(line)
            else:
                line = [kameras[i].name,kameras[i].snapshot_active,kameras[i].snapshot_period,kameras[i].film_active]
                csv_writer.writerow(line)



def settingsFromUser(changes,previous):
    final = previous
    for i in changes:
        for x in changes[i]:
            final[i][x] = changes[i][x]
    return final



app = typer.Typer()


@app.command()
def display():
    console = Console()
    all_cameras = createRtspCameras(getRtspStreams(),getRtspPort(),CameraRTSP)
    csv_path = os.path.dirname(os.path.abspath(__file__))+'/settings.csv'
    writeSettingsTocsv(all_cameras,readSetting(csv_path),csv_path)
    read_settings = readSetting(csv_path)
    table = Table("Kamera:", "Robienie snapshotów","Czas między snapshotami","Nagrywanie")
    for i in read_settings:
        table.add_row(i,str(read_settings[i]['snapshot_active']),str(read_settings[i]['snapshot_period']),str(read_settings[i]['film_active']))
    console.print(table)
    print('Folder zapisu snapshotów: ')
    print(os.getcwd()+'/snapshots')


@app.command()
def run():

    all_cameras = createRtspCameras(getRtspStreams(),getRtspPort(),CameraRTSP)
    csv_path = os.path.dirname(os.path.abspath(__file__))+'/settings.csv'
    writeSettingsTocsv(all_cameras,readSetting(csv_path),csv_path)
    changeToSaveDirectory(os.getcwd())
    setCameraSettings(all_cameras,readSetting(csv_path))
    runSnapshotThreads(all_cameras,snapshotLoop)
    runSnapshotThreads(all_cameras,cameraLoop)
    print('hhh')
    time.sleep(4294967)

@app.command()
def change(
    nazwa: str,
    snapshots: Annotated[bool, typer.Option(prompt=True)],
    odstępy: Annotated[float, typer.Option(prompt=True)],
    nagrywanie: Annotated[bool, typer.Option(prompt=True)]):
    
    all_cameras = createRtspCameras(getRtspStreams(),getRtspPort(),CameraRTSP)
    csv_path = os.path.dirname(os.path.abspath(__file__))+'/settings.csv'
    writeSettingsTocsv(all_cameras,readSetting(csv_path),csv_path)

    csv_settings=  settingsFromUser({nazwa:{'snapshot_active':snapshots,'snapshot_period':odstępy,'film_active':nagrywanie}},readSetting(csv_path))
    print(csv_settings)
    print('hello')
    writeSettingsTocsv(all_cameras,csv_settings,csv_path)






if __name__=='__main__':
    app()

