"""
Mellow music video v4 — varied, organic transitions.

Same take construction as v3 (section-boundary takes, slowed Ken Burns,
flipped/re-zoomed repeats) but the transitions between takes now VARY across
a curated set of soft/dreamy xfade types instead of a single plain crossfade,
run a touch longer, and land on beat-snapped boundaries.

Usage: python build_v4.py <audio> <out.mp4> clipA.mp4 ...
"""
import sys, os, json, subprocess

AUDIO, OUT = sys.argv[1], sys.argv[2]
CLIPS = sys.argv[3:]
SIZE, FPS = 1080, 24
XF = 1.4                      # crossfade seconds (softer, longer)
WORK = "segs4"
os.makedirs(WORK, exist_ok=True)

# single transition applied throughout (override with TRANSITION env var)
TRANSITIONS = [os.environ.get("TRANSITION", "fade")]

data = json.load(open("beats.json"))
beats = sorted(data["beats"])
sections = sorted(data["sections"])

dur = float(subprocess.run(
    ["ffprobe","-v","error","-show_entries","format=duration",
     "-of","default=noprint_wrappers=1:nokey=1", AUDIO],
    capture_output=True, text=True).stdout.strip())
clip_dur = min(float(subprocess.run(
    ["ffprobe","-v","error","-show_entries","format=duration",
     "-of","default=noprint_wrappers=1:nokey=1", c],
    capture_output=True, text=True).stdout.strip()) for c in CLIPS)

def snap_beat(t):
    return min(beats, key=lambda b: abs(b - t))

# --- boundaries: merge tiny sections, split long ones, snap to beats ---
raw = [0.0] + [s for s in sections if 0 < s < dur] + [dur]
raw = sorted(set(round(x, 3) for x in raw))
merged = [raw[0]]
for t in raw[1:]:
    if t - merged[-1] < 6.0:
        if t == dur:
            merged[-1] = dur
        continue
    merged.append(t)
if merged[-1] != dur:
    merged.append(dur)
bounds = [merged[0]]
for a, b in zip(merged[:-1], merged[1:]):
    if b - a > 22.0:
        mid = snap_beat((a + b) / 2)
        if a + 4 < mid < b - 4:
            bounds.append(mid)
    bounds.append(b)
# snap interior boundaries tight to the nearest beat
bounds = [bounds[0]] + [snap_beat(t) for t in bounds[1:-1]] + [bounds[-1]]
bounds = sorted(set(round(x, 3) for x in bounds))
segs = list(zip(bounds[:-1], bounds[1:]))
print(f"{len(segs)} takes, boundaries: {[round(x,1) for x in bounds]}", flush=True)

# --- clip assignment: no adjacent repeat, spread across the clips ---
n = len(CLIPS)
order, c = [], 0
for i in range(len(segs)):
    order.append(c)
    c = (c + (2 if i % 2 == 0 else 1)) % n
seen = {}

# --- render each take (native 1x speed; ping-pong to fill long takes) ---
# No per-frame zoom and no slow-motion -> no zoompan jitter, no frame-dup judder.
files = []
usable = clip_dur - 0.2
for idx, (a, b) in enumerate(segs):
    is_last = idx == len(segs) - 1
    v = b - a
    Lreq = v if is_last else v + XF
    ci = order[idx]
    clip = CLIPS[ci]
    seen[ci] = seen.get(ci, 0) + 1
    flip = "hflip," if seen[ci] % 2 == 0 else ""
    frame = (f"{flip}scale={SIZE}:{SIZE}:force_original_aspect_ratio=increase,"
             f"crop={SIZE}:{SIZE},fps={FPS},setsar=1")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if Lreq <= usable:
        # play a native-speed window of the clip
        ss = (idx * 2.9) % max(0.1, usable - Lreq)
        cmd += ["-ss", f"{ss:.3f}", "-i", clip,
                "-vf", f"{frame},format=yuv420p"]
        mode = "1x"
    else:
        # ping-pong (forward + reverse) to fill at native speed, seamless
        cmd += ["-i", clip,
                "-vf", f"{frame},split[a][b];[b]reverse[r];[a][r]"
                       f"concat=n=2:v=1,format=yuv420p"]
        mode = "pingpong"
    out = f"{WORK}/take_{idx:02d}.mp4"
    cmd += ["-an", "-t", f"{Lreq:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-crf", "19", "-preset", "medium",
            "-video_track_timescale", "12288", out]
    subprocess.run(cmd, check=True)
    files.append(out)
    print(f"take {idx}: clip{ci} {v:.1f}s {mode} {'flip' if flip else ''}", flush=True)

# --- chain takes with VARIED transitions ---
inputs = []
for fpath in files:
    inputs += ["-i", fpath]
fc, prev = [], "[0:v]"
cum = 0.0
used = []
for k in range(1, len(files)):
    cum += (segs[k-1][1] - segs[k-1][0])
    off = max(0.0, cum - XF / 2)
    tr = TRANSITIONS[(k - 1) % len(TRANSITIONS)]
    used.append(tr)
    lbl = f"[x{k}]"
    fc.append(f"{prev}[{k}:v]xfade=transition={tr}:duration={XF}:offset={off:.3f}{lbl}")
    prev = lbl
print("transitions:", used, flush=True)
filtergraph = ";".join(fc)
video = f"{WORK}/video.mp4"
subprocess.run(
    ["ffmpeg","-y","-loglevel","error", *inputs,
     "-filter_complex", filtergraph, "-map", prev,
     "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p", video],
    check=True)

# --- mux song ---
subprocess.run(
    ["ffmpeg","-y","-loglevel","error","-i", video, "-i", AUDIO,
     "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k",
     "-shortest", OUT], check=True)
print("done ->", OUT, flush=True)
