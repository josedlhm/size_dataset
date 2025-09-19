#!/usr/bin/env python3
# extract_svo2_dataset.py — SVO2 → per-ID/images + per-ID/depth (sample every 20 frames)

from pathlib import Path
import sys, numpy as np, cv2
import pyzed.sl as sl

MAX_MM = 2000.0   # cap depth at 2 m
STRIDE = 20       # save 1 of every 20 frames

def extract_one(svo_path: Path, out_root: Path):
    sid = svo_path.stem
    img_dir   = out_root / sid / "images"; img_dir.mkdir(parents=True, exist_ok=True)
    depth_dir = out_root / sid / "depth";  depth_dir.mkdir(parents=True, exist_ok=True)

    # --- Init playback ---
    init = sl.InitParameters()
    init.set_from_svo_file(str(svo_path))
    init.svo_real_time_mode   = False
    init.depth_mode           = sl.DEPTH_MODE.NEURAL_PLUS
    init.coordinate_units     = sl.UNIT.MILLIMETER
    init.coordinate_system    = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP
    init.async_image_retrieval = False

    cam = sl.Camera()
    if cam.open(init) != sl.ERROR_CODE.SUCCESS:
        print(f"[OPEN FAIL] {svo_path.name}")
        return

    runtime = sl.RuntimeParameters()
    z_img, z_dep = sl.Mat(), sl.Mat()
    frame = 0
    total = cam.get_svo_number_of_frames()

    while True:
        err = cam.grab(runtime)
        if err == sl.ERROR_CODE.END_OF_SVOFILE_REACHED: break
        if err != sl.ERROR_CODE.SUCCESS: break

        if frame % STRIDE == 0:
            name = f"{frame:06d}"

            # --- RGB: BGRA → BGR ---
            cam.retrieve_image(z_img, sl.VIEW.LEFT)
            img_bgra = z_img.get_data()
            img_bgr  = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
            cv2.imwrite(str(img_dir / f"{name}.png"), img_bgr,
                        [cv2.IMWRITE_PNG_COMPRESSION, 0])

            # --- Depth: float32 mm; sanitize + cap to 2 m ---
            cam.retrieve_measure(z_dep, sl.MEASURE.DEPTH)
            dep = z_dep.get_data().astype(np.float32, copy=True)
            np.nan_to_num(dep, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
            dep[dep > MAX_MM] = 0.0
            np.save(depth_dir / f"{name}.npy", dep)

        frame += 1
        if total > 0 and frame >= total: break

    cam.close()
    print(f"[OK] {sid}: saved {frame//STRIDE} frames → {img_dir} / {depth_dir}")

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dataset")
    raw  = root / "raw"
    out  = root / "samples"

    if not raw.exists():
        sys.exit(f"raw folder not found: {raw}")
    svos = sorted(raw.glob("*.svo*"))
    if not svos:
        sys.exit(f"no .svo/.svo2 files in {raw}")

    for svo in svos:
        extract_one(svo, out)

if __name__ == "__main__":
    main()
