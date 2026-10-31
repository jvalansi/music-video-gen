"""
Edit for 'Room at the Table': lyric-driven takes instead of detected sections.

Cuts follow the story (whisper segment times, snapped to beats), so each scene
lands on the line it illustrates. Rendering follows build_v4: native speed,
plain fade, ping-pong only where a take outruns its clip, no zoompan.

Usage: python build_room.py <audio> <beats.json> <out.mp4>
"""
import sys, os, json, subprocess

AUDIO, BEATS, OUT = sys.argv[1:4]
SIZE, FPS, XF = 1080, 24, 1.0
WORK = "room/segs"
os.makedirs(WORK, exist_ok=True)
C = lambda n: f"room/room_{n}.mp4"

# (cut time in s, clip, hflip) -- times from room/transcript.json
TAKES = [
    (0.0,  C("1_hill"),     False),  # intro: hey-ya hey-yo
    (16.0, C("2_traveler"), False),  # came up the hill with a coat full of rain
    (24.8, C("3_door"),     False),  # set down the basket beside the old door
    (37.0, C("4_hearth"),   False),  # chorus: come sit where the warm coals glow
    (48.0, C("1_hill"),     True),   # break / the hard wind passed
    (63.0, C("3_door"),     True),   # your laugh found the rafters
    (80.0, C("4_hearth"),   True),   # chorus 2
    (90.0, C("1_hill"),     False),  # outro
]

beats = sorted(json.load(open(BEATS))["beats"])
probe = lambda f: float(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", f],
    capture_output=True, text=True, check=True).stdout)
dur = probe(AUDIO)
snap = lambda t: min(beats, key=lambda b: abs(b - t))
bounds = [0.0] + [round(snap(t), 3) for t, _, _ in TAKES[1:]] + [dur]
assert all(a < b for a, b in zip(bounds, bounds[1:])), f"cuts collide after beat snap: {bounds}"
segs = list(zip(bounds[:-1], bounds[1:]))

files = []
for idx, ((a, b), (_, clip, flip)) in enumerate(zip(segs, TAKES)):
    # every take after the first starts XF/2 early, so the last one needs XF/2 extra to reach dur
    L = (b - a) + (XF / 2 if idx == len(segs) - 1 else XF)
    usable = probe(clip) - 0.2
    frame = (f"{'hflip,' if flip else ''}scale={SIZE}:{SIZE}:force_original_aspect_ratio=increase,"
             f"crop={SIZE}:{SIZE},fps={FPS},setsar=1")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if L <= usable:
        # flipped repeats start later in the clip so they don't replay the same frames
        ss = (usable - L) if flip else 0.0
        cmd += ["-ss", f"{ss:.3f}", "-i", clip, "-vf", f"{frame},format=yuv420p"]
        mode = "1x"
    else:
        cmd += ["-i", clip, "-vf", f"{frame},split[a][b];[b]reverse[r];[a][r]"
                                   f"concat=n=2:v=1,format=yuv420p"]
        mode = "pingpong"
    out = f"{WORK}/take_{idx:02d}.mp4"
    cmd += ["-an", "-t", f"{L:.3f}", "-r", str(FPS), "-c:v", "libx264", "-crf", "19",
            "-preset", "medium", "-video_track_timescale", "12288", out]
    subprocess.run(cmd, check=True)
    files.append(out)
    print(f"take {idx}: {a:5.1f}-{b:5.1f} {os.path.basename(clip)} {mode}{' flip' if flip else ''}", flush=True)

inputs = [x for f in files for x in ("-i", f)]
fc, prev, cum = [], "[0:v]", 0.0
for k in range(1, len(files)):
    cum += segs[k - 1][1] - segs[k - 1][0]
    fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={cum - XF / 2:.3f}[x{k}]")
    prev = f"[x{k}]"
# fade in from / out to black
fc.append(f"{prev}fade=t=in:d=1.5,fade=t=out:st={dur - 2.5:.3f}:d=2.5[v]")
video = f"{WORK}/video.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc),
                "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p", video], check=True)
tmp = OUT + ".tmp.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", AUDIO,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", tmp], check=True)
os.replace(tmp, OUT)
print("done ->", OUT, flush=True)
