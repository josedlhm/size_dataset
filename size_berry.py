#!/usr/bin/env python3
import sys, time, csv, json, re
from pathlib import Path
import pyzed.sl as sl

SN = 50918724                               # ← your ZEDXMini_SN50918724 serial
ROOT = Path("dataset"); RAW=ROOT/"raw"; LBL=ROOT/"labels"; CSV=ROOT/"metadata.csv"

def ensure_dirs():
    RAW.mkdir(parents=True, exist_ok=True); LBL.mkdir(parents=True, exist_ok=True)

def f(prompt):
    while True:
        try: return float(input(prompt).strip())
        except: pass

def main():
    ensure_dirs()
    cam = sl.Camera()
    init = sl.InitParameters(); init.set_from_serial_number(SN)
    init.depth_mode = sl.DEPTH_MODE.NONE; init.camera_resolution = sl.RESOLUTION.HD1200
    init.camera_fps = 15; init.async_image_retrieval = False
    if cam.open(init) != sl.ERROR_CODE.SUCCESS: print("open failed"); sys.exit(1)

    dur = 15.0
    try:
        while True:
            sid = input("ID (blank=quit): ").strip()
            if not sid: break
            svo = RAW/f"{sid}.svo2"
            if svo.exists(): print("exists"); continue

            w = f("weight g: "); c = f("caliber mm: ")

            if cam.enable_recording(sl.RecordingParameters(str(svo), sl.SVO_COMPRESSION_MODE.H265)) != sl.ERROR_CODE.SUCCESS:
                print("rec fail"); continue
            t0=time.time(); rt=sl.RuntimeParameters()
            try:
                while time.time()-t0 < dur: cam.grab(rt)
            finally:
                cam.disable_recording()

            (LBL/f"{sid}.json").write_text(json.dumps({
                "sample_id": sid, "weight_g": w, "caliber_mm": c,
                "date": time.strftime("%Y-%m-%d"),
                "svo2_file": str(Path("raw")/svo.name),
                "capture": {"codec":"H265","duration_s":dur}
            }, indent=2))

            new = not CSV.exists()
            with open(CSV, "a", newline="") as f:
                wtr = csv.DictWriter(f, fieldnames=["sample_id","weight_g","caliber_mm","date","svo2"])
                if new: wtr.writeheader()
                wtr.writerow({"sample_id":sid,"weight_g":w,"caliber_mm":c,"date":time.strftime("%Y-%m-%d"),"svo2":str(Path('raw')/svo.name)})
            print("ok")
    finally:
        cam.close()

if __name__ == "__main__":
    main()
