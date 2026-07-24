"""
Build a beat-synced music video from still images.

- Images switch on section boundaries.
- Continuous Ken Burns zoom within each section.
- A quick zoom "punch" (+ brightness flash) on every detected beat.

Frames are piped as raw RGB into ffmpeg, which muxes the audio.
Usage: python build_beat_video.py <audio> <out.mp4> img1 img2 ...
"""
import sys, json, subprocess, math
import numpy as np
from PIL import Image

AUDIO, OUT = sys.argv[1], sys.argv[2]
IMG_PATHS = sys.argv[3:]

FPS = 24
SIZE = 1080                      # square output
data = json.load(open("beats.json"))
beats = data["beats"]
sections = data["sections"]

# total duration from audio
dur = float(subprocess.run(
    ["ffprobe","-v","error","-show_entries","format=duration",
     "-of","default=noprint_wrappers=1:nokey=1", AUDIO],
    capture_output=True, text=True).stdout.strip())

# segment boundaries: sections + end
bounds = sorted(set([0.0] + [s for s in sections if 0 < s < dur] + [dur]))
segments = list(zip(bounds[:-1], bounds[1:]))

# load images as square arrays
imgs = [Image.open(p).convert("RGB").resize((1024, 1024)) for p in IMG_PATHS]

beats_arr = np.array(beats)

def nearest_prev_beat(t):
    prev = beats_arr[beats_arr <= t]
    return prev[-1] if len(prev) else -10.0

def seg_for(t):
    for i, (a, b) in enumerate(segments):
        if a <= t < b:
            return i, a, b
    return len(segments)-1, segments[-1][0], segments[-1][1]

BASE_Z0, BASE_Z1 = 1.06, 1.16     # ken burns zoom range per segment
PUNCH_A, PUNCH_TAU = 0.055, 0.11  # beat punch amplitude / decay (s)
FLASH_A = 0.14

nframes = int(dur * FPS)
ff = subprocess.Popen([
    "ffmpeg","-y","-loglevel","error",
    "-f","rawvideo","-pix_fmt","rgb24","-s",f"{SIZE}x{SIZE}","-r",str(FPS),"-i","-",
    "-i", AUDIO,
    "-map","0:v","-map","1:a",
    "-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-preset","veryfast",
    "-c:a","aac","-b:a","192k","-shortest", OUT
], stdin=subprocess.PIPE)

for f in range(nframes):
    t = f / FPS
    si, a, b = seg_for(t)
    img = imgs[si % len(imgs)]
    # ken burns base zoom across the segment
    frac = (t - a) / max(b - a, 1e-6)
    base = BASE_Z0 + (BASE_Z1 - BASE_Z0) * frac
    # gentle pan (drift) unique per segment
    pan = 0.06 * math.sin(frac * math.pi + si)
    # beat punch
    tb = nearest_prev_beat(t)
    dt = t - tb
    punch = PUNCH_A * math.exp(-dt / PUNCH_TAU) if dt >= 0 else 0.0
    flash = FLASH_A * math.exp(-dt / PUNCH_TAU) if dt >= 0 else 0.0
    z = base + punch

    # crop a centered window of size 1024/z, with horizontal pan
    win = 1024 / z
    cx = 512 + pan * (1024 - win) * 0.5
    cy = 512
    left = max(0, min(1024 - win, cx - win/2))
    top  = max(0, min(1024 - win, cy - win/2))
    crop = img.crop((left, top, left+win, top+win)).resize((SIZE, SIZE), Image.BILINEAR)

    arr = np.asarray(crop).astype(np.float32)
    if flash > 0:
        arr = np.clip(arr * (1 + flash), 0, 255)
    ff.stdin.write(arr.astype(np.uint8).tobytes())

    if f % 240 == 0:
        print(f"frame {f}/{nframes}", flush=True)

ff.stdin.close()
ff.wait()
print("done ->", OUT)
