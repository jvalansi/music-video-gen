"""
Mellow beat-synced music video v3.

- Cuts land on SECTION boundaries (musical changes), ~12-17s apart.
- Crossfade dissolves between takes (no hard cut, no blank frame).
- Each take is slowed + given a slow Ken Burns zoom (alternating in/out) so
  the clip evolves; repeats of the same clip are flipped / re-zoomed so the
  4-clip rotation is far less obvious.

Usage: python build_v3.py <audio> <out.mp4> clipA.mp4 ...
"""
import sys, os, json, subprocess

AUDIO, OUT = sys.argv[1], sys.argv[2]
CLIPS = sys.argv[3:]
SIZE, FPS = 1080, 24
XF = 1.1                      # crossfade seconds
WORK = "segs3"
os.makedirs(WORK, exist_ok=True)

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

# --- build boundaries: merge tiny sections, split long ones ---
raw = [0.0] + [s for s in sections if 0 < s < dur] + [dur]
raw = sorted(set(round(x, 3) for x in raw))
# merge boundaries closer than 6s (keep earlier)
merged = [raw[0]]
for t in raw[1:]:
    if t - merged[-1] < 6.0:
        if t == dur:
            merged[-1] = dur
        continue
    merged.append(t)
if merged[-1] != dur:
    merged.append(dur)
# split segments longer than 22s at a beat near the midpoint
bounds = [merged[0]]
for a, b in zip(merged[:-1], merged[1:]):
    if b - a > 22.0:
        mid = snap_beat((a + b) / 2)
        if a + 4 < mid < b - 4:
            bounds.append(mid)
    bounds.append(b)
bounds = sorted(set(bounds))
segs = list(zip(bounds[:-1], bounds[1:]))
print(f"{len(segs)} takes, boundaries: {[round(x,1) for x in bounds]}", flush=True)

# --- clip assignment: no adjacent repeat, spread across the 4 ---
n = len(CLIPS)
order, c = [], 0
for i in range(len(segs)):
    order.append(c)
    c = (c + (2 if i % 2 == 0 else 1)) % n
seen = {}

# --- render each take: slow to fill, ken burns zoom, optional flip ---
files = []
for idx, (a, b) in enumerate(segs):
    is_last = idx == len(segs) - 1
    v = b - a
    Lreq = v if is_last else v + XF
    ci = order[idx]
    clip = CLIPS[ci]
    ratio = max(1.0, Lreq / (clip_dur - 0.15))     # slow factor (>=1)
    ss = 0.0 if ratio > 1.001 else ((idx * 2.9) % max(0.1, clip_dur - Lreq - 0.15))
    zoom_in = (idx % 2 == 0)
    nf = max(1, int(Lreq * FPS))
    if zoom_in:
        Z = f"1.04+0.10*on/{nf}"
    else:
        Z = f"1.14-0.10*on/{nf}"
    seen[ci] = seen.get(ci, 0) + 1
    flip = "hflip," if seen[ci] % 2 == 0 else ""     # flip repeats of a clip
    vf = (
        f"setpts={ratio:.4f}*PTS,fps={FPS},{flip}"
        f"zoompan=z='{Z}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={SIZE}x{SIZE}:fps={FPS},setsar=1,format=yuv420p"
    )
    out = f"{WORK}/take_{idx:02d}.mp4"
    cmd = ["ffmpeg","-y","-loglevel","error"]
    if ratio <= 1.001:
        cmd += ["-ss", f"{ss:.3f}"]
    cmd += ["-i", clip, "-vf", vf, "-an", "-t", f"{Lreq:.3f}",
            "-r", str(FPS), "-c:v","libx264","-crf","19","-preset","medium",
            "-video_track_timescale","12288", out]
    subprocess.run(cmd, check=True)
    files.append(out)
    print(f"take {idx}: clip{ci} {v:.1f}s slow x{ratio:.2f} {'flip' if flip else ''} "
          f"{'zin' if zoom_in else 'zout'}", flush=True)

# --- crossfade-chain all takes ---
inputs = []
for fpath in files:
    inputs += ["-i", fpath]
fc, prev, off = [], "[0:v]", 0.0
cum = 0.0
for k in range(1, len(files)):
    cum += (segs[k-1][1] - segs[k-1][0])     # visible dur of take k-1
    off = max(0.0, cum - XF / 2)
    lbl = f"[x{k}]"
    fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{lbl}")
    prev = lbl
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
