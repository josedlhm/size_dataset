#!/usr/bin/env python3
import sys, csv, json, time, os, re
from pathlib import Path
from datetime import datetime
from signal import signal, SIGINT
import pyzed.sl as sl

# --- config ---
CAM_ID = "ZEDXMini_SN50918724"         # we extract the SN from this
ROOT = Path("./dataset"); RAW=ROOT/"raw"; LBL=ROOT/"labels"; CSV=ROOT/"metadata.csv"

cam = sl.Camera(); rec_on = False
def quit(*_):
    global rec_on
    try:
        if rec_on: cam.disable_recording()
        cam.close()
    except: pass
    sys.exit(0)
signal(SIGINT, quit)

def serial_from(cam_id: str) -> int:
    m = re.search(r"(\d+)$", cam_id)
    if not m: print("No trailing digits (serial) in CAM_ID"); sys.exit(1)
    return int(m.group(1))

def assert_connected(sn: int):
    for d in sl.Camera.get_device_list():
        if d.serial_number == sn: return
    print(f"Camera with SN {sn} not found"); sys.exit(1)

def ensure_dirs():
    RAW.mkdir(parents=True, exist_ok=True); LBL.mkdir(parents=True, exist_ok=True)

def wjson(sid,payload): (LBL/f"{sid}.json").write_text(json.dumps(payload,indent=2))
def addcsv(row):
    new = not CSV.exists()
    with open(CSV,"a",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["sample_id","weight_g","caliber_mm","date","svo2"])
        if new: w.writeheader()
        w.writerow(row)

def fnum(prompt):
    while True:
        try: return float(input(prompt).strip())
        except: pass

def record(svo_path: Path, secs: float):
    global rec_on
    err = cam.enable_recording(sl.RecordingParameters(str(svo_path), sl.SVO_COMPRESSION_MODE.H265))
    if err != sl.ERROR_CODE.SUCCESS: print(err); sys.exit(1)
    rec_on = True
    rt = sl.RuntimeParameters()
    t0=time.time()
    try:
        while time.time()-t0 < secs: cam.grab(rt)
    finally:
        cam.disable_recording(); rec_on=False

def main():
    ensure_dirs()
    sn = serial_from(CAM_ID)
    assert_connected(sn)
    init = sl.InitParameters(); init.set_from_serial_number(sn)
    init.depth_mode = sl.DEPTH_MODE.NONE; init.async_image_retrieval=False
    if cam.open(init) != sl.ERROR_CODE.SUCCESS: print("Open failed"); sys.exit(1)

    d = input("Duration seconds (Enter=15): ").strip()
    dur = 15.0 if d=="" else max(0.5,float(d))
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        while True:
            sid = input("\nBerry ID (blank=quit): ").strip()
            if not sid: break
            svo = RAW/f"{sid}.svo2"
            if svo.exists(): print("ID exists"); continue
            w=fnum("Weight g: "); c=fnum("Caliber mm: ")
            record(svo,dur)
            row={"sample_id":sid,"weight_g":w,"caliber_mm":c,"date":today,"svo2":str(Path('raw')/svo.name)}
            wjson(sid,{**row,"capture":{"codec":"H265","duration_s":dur}})
            addcsv(row)
            print("ok")
    finally:
        cam.close()

if __name__=="__main__":
    main()
