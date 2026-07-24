"""
Beat-synced music video from motion clips.

- Cuts between clips on beats (faster cuts in the high-energy midsection).
- A quick white flash on every cut for punch.
- Output 1080x1080, then the song is muxed in.

Usage: python build_from_clips.py <audio> <out.mp4> clipA.mp4 clipB.mp4 ...
"""
import sys, os, json, subprocess

AUDIO, OUT = sys.argv[1], sys.argv[2]
CLIPS = sys.argv[3:]
SIZE, FPS = 1080, 24
WORK = "segs"
os.makedirs(WORK, exist_ok=True)

data = json.load(open("beats.json"))
beats = data["beats"]

dur = float(subprocess.run(
    ["ffprobe","-v","error","-show_entries","format=duration",
     "-of","default=noprint_wrappers=1:nokey=1", AUDIO],
    capture_output=True, text=True).stdout.strip())

clip_dur = min(float(subprocess.run(
    ["ffprobe","-v","error","-show_entries","format=duration",
     "-of","default=noprint_wrappers=1:nokey=1", c],
    capture_output=True, text=True).stdout.strip()) for c in CLIPS)

# Build cut boundaries from beats: step 2 beats in the energetic midsection
# (42-122s), step 4 beats elsewhere. Always land on a beat.
HIGH_LO, HIGH_HI = 42.0, 122.0
bounds = [0.0]
i = 0
while i < len(beats):
    t = beats[i]
    if t <= bounds[-1]:
        i += 1
        continue
    bounds.append(t)
    step = 2 if HIGH_LO <= t < HIGH_HI else 4
    i += step
if dur - bounds[-1] > 0.4:
    bounds.append(dur)
else:
    bounds[-1] = dur

segments = list(zip(bounds[:-1], bounds[1:]))
print(f"{len(segments)} segments over {dur:.1f}s", flush=True)

# Extract each segment from a cycling clip, with a white-flash on the cut.
seg_files = []
for idx, (a, b) in enumerate(segments):
    seg_len = b - a
    clip = CLIPS[idx % len(CLIPS)]
    # vary the in-point so repeated clips show different moments
    headroom = max(0.0, clip_dur - seg_len - 0.15)
    ss = ((idx * 2.7) % headroom) if headroom > 0.1 else 0.0
    out = f"{WORK}/seg_{idx:03d}.mp4"
    vf = (f"scale={SIZE}:{SIZE}:force_original_aspect_ratio=increase,"
          f"crop={SIZE}:{SIZE},fps={FPS},format=yuv420p,"
          f"fade=t=in:st=0:d=0.10:color=white")
    subprocess.run(
        ["ffmpeg","-y","-loglevel","error","-ss",f"{ss:.3f}","-t",f"{seg_len:.3f}",
         "-i", clip, "-vf", vf, "-an",
         "-c:v","libx264","-crf","19","-preset","veryfast",
         "-video_track_timescale","12288", out],
        check=True)
    seg_files.append(out)
    if idx % 10 == 0:
        print(f"seg {idx}/{len(segments)}", flush=True)

# Concat segments
listfile = f"{WORK}/list.txt"
with open(listfile, "w") as f:
    for s in seg_files:
        f.write(f"file '{os.path.basename(s)}'\n")
concat = f"{WORK}/concat.mp4"
subprocess.run(
    ["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0",
     "-i", listfile, "-c","copy", concat], check=True)

# Mux song audio
subprocess.run(
    ["ffmpeg","-y","-loglevel","error","-i", concat, "-i", AUDIO,
     "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k",
     "-shortest", OUT], check=True)
print("done ->", OUT, flush=True)
