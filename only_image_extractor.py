#!/usr/bin/env python3
# simple_extract_images.py — save every 20th frame from all .svo2s, rotated 90° clockwise

from pathlib import Path
import cv2, pyzed.sl as sl

RAW_DIR = Path("dataset/raw")       # <- change this if needed
OUT_DIR = Path("dataset/samples")
STRIDE  = 20                        # save every 20th frame

def extract_images(svo_path: Path):
    sid = svo_path.stem
    out_img = OUT_DIR / sid / "images"
    out_img.mkdir(parents=True, exist_ok=True)

    init = sl.InitParameters()
    init.set_from_svo_file(str(svo_path))
    init.svo_real_time_mode = False
    init.depth_mode = sl.DEPTH_MODE.NONE

    cam = sl.Camera()
    if cam.open(init) != sl.ERROR_CODE.SUCCESS:
        print(f"[FAIL] {svo_path}")
        return

    rt = sl.RuntimeParameters()
    mat = sl.Mat()
    frame = 0
    while True:
        err = cam.grab(rt)
        if err == sl.ERROR_CODE.END_OF_SVOFILE_REACHED: break
        if err != sl.ERROR_CODE.SUCCESS: break

        if frame % STRIDE == 0:
            name = f"{sid}_{frame:06d}.png"
            cam.retrieve_image(mat, sl.VIEW.LEFT)
            img = mat.get_data()
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img_rot = cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(str(out_img / name), img_rot,
                        [cv2.IMWRITE_PNG_COMPRESSION, 0])
        frame += 1

    cam.close()
    print(f"[OK] {sid}: saved images in {out_img}")

def main():
    for svo in sorted(RAW_DIR.glob("*.svo*")):
        extract_images(svo)

if __name__ == "__main__":
    main()
