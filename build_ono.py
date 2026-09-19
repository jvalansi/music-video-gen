"""
Beat-locked edit for Ono-meno-me.

Differs from build_v4 in one respect: the shuffle clip is not just cut on beat,
its footwork runs at the song's tempo. hero_loop.mp4 is pre-stretched so a
footfall lands every beat and its length is a whole number of beats at 9
frames/beat, so looping it never drifts. Hero takes are cut out of one
continuously looped, phase-aligned track, which keeps every take in step with
the grid. B-roll (the dream clips) carries the breakdowns and has no tempo to
respect, so it ping-pongs as before.

Usage: python build_ono.py <audio> <out.mp4>
"""
import json, os, subprocess, numpy as np

AUDIO = os.sys.argv[1]
OUT = os.sys.argv[2]
SIZE, WORK = 1080, "segs_ono"
os.makedirs(WORK, exist_ok=True)

T = json.load(open("hero_timing.json"))
PERIOD, FPS, FPB = T["period"], T["fps"], T["fpb"]
HERO, LOOP_DUR = "hero_loop.mp4", T["loop_dur"]
BROLL = ["dream_2_clouds_clip.mp4", "dream_3_water_clip.mp4",
         "dream_1_figure_clip.mp4", "dream_4_neon_clip.mp4"]
XF = 2 * PERIOD                                   # 2-beat dissolve

d = json.load(open("beats_ono.json"))
beats, sections, DUR = sorted(d["beats"]), sorted(d["sections"]), d["duration"]
snap = lambda t: min(beats, key=lambda b: abs(b - t))
# every cut must also be a whole frame, or the loop phase slips
qf = lambda t: round(t * FPS) / FPS

# --- boundaries: drop tiny sections, split long ones, snap to beats ---
raw = sorted({round(x, 3) for x in [0.0] + [s for s in sections if 0 < s < DUR] + [DUR]})
merged = [raw[0]]
for t in raw[1:]:
    if t - merged[-1] < 8.0:
        if t == DUR:
            merged[-1] = DUR
        continue
    merged.append(t)
if merged[-1] != DUR:
    merged.append(DUR)
bounds = [merged[0]]
for a, b in zip(merged[:-1], merged[1:]):
    if b - a > 24.0:
        n = int(b - a) // 20 + 1
        for k in range(1, n):
            bounds.append(snap(a + (b - a) * k / n))
    bounds.append(b)
bounds = sorted({qf(snap(t)) if 0 < t < DUR else qf(t) for t in bounds})
segs = list(zip(bounds[:-1], bounds[1:]))

# --- who carries each take: b-roll on the two low-energy breakdowns + intro/outro ---
QUIET = [(0.0, 23.2), (79.6, 101.9), (124.6, 146.0), (181.3, DUR)]
is_quiet = lambda a, b: any(qa - 1 < (a + b) / 2 < qb + 1 for qa, qb in QUIET)
plan = [("broll" if is_quiet(a, b) else "hero") for a, b in segs]
print(f"{len(segs)} takes: " + " ".join(
    f"{a:.0f}-{b:.0f}{'H' if p == 'hero' else 'b'}" for (a, b), p in zip(segs, plan)), flush=True)

# --- one continuous hero track, phase-shifted so footfalls sit on beats ---
beat_phase = beats[0] % PERIOD
s0 = (T["phi"] - beat_phase) % PERIOD
s0 = round(s0 * FPS) / FPS
hero_track = f"{WORK}/hero_track.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                "-stream_loop", str(int(DUR // LOOP_DUR) + 2), "-i", HERO,
                "-vf", f"trim=start={s0:.5f},setpts=PTS-STARTPTS,"
                       f"scale={SIZE}:{SIZE},fps={FPS:.6f},format=yuv420p,setsar=1",
                "-an", "-t", f"{DUR + 5:.3f}", "-c:v", "libx264", "-crf", "18",
                "-preset", "medium", "-video_track_timescale", "12288", hero_track], check=True)
print(f"hero track built, phase offset {s0*1000:.0f}ms", flush=True)

# --- b-roll is only 10s, so pre-render a ping-pong of each and loop that;
#     a take longer than its source silently comes out short and collapses the
#     xfade chain, so lengths are asserted below.
pp = []
for i, clip in enumerate(BROLL):
    out = f"{WORK}/pp_{i}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip,
                    "-vf", f"scale={SIZE}:{SIZE}:force_original_aspect_ratio=increase,"
                           f"crop={SIZE}:{SIZE},fps={FPS:.6f},setsar=1,"
                           f"split[x][y];[y]reverse[r];[x][r]concat=n=2:v=1,format=yuv420p",
                    "-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                    "-video_track_timescale", "12288", out], check=True)
    pp.append(out)

def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nw=1:nk=1", path],
                                capture_output=True, text=True).stdout)

# --- render takes ---
files, bi = [], 0
for idx, (a, b) in enumerate(segs):
    length = (b - a) + (0 if idx == len(segs) - 1 else XF)
    out = f"{WORK}/take_{idx:02d}.mp4"
    if plan[idx] == "hero":
        # cut the window at its own song time: phase carries over untouched
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.5f}", "-i", hero_track,
               "-vf", f"fps={FPS:.6f},format=yuv420p", "-t", f"{length:.5f}"]
    else:
        src = pp[bi % len(pp)]
        flip = "hflip," if (bi // len(pp)) % 2 else ""
        bi += 1
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-stream_loop", str(int(length // duration(src)) + 1), "-i", src,
               "-vf", f"{flip}fps={FPS:.6f},format=yuv420p", "-t", f"{length:.5f}"]
    subprocess.run(cmd + ["-an", "-r", f"{FPS:.6f}", "-c:v", "libx264", "-crf", "19",
                          "-preset", "medium", "-video_track_timescale", "12288", out], check=True)
    got = duration(out)
    assert got >= length - 2.0 / FPS, f"take {idx} short: {got:.3f}s < {length:.3f}s"
    files.append(out)

# --- chain with dissolves landing on the beat boundaries ---
inputs, fc, prev, cum = [], [], "[0:v]", 0.0
for f in files:
    inputs += ["-i", f]
for k in range(1, len(files)):
    cum += segs[k - 1][1] - segs[k - 1][0]
    off = max(0.0, cum - XF / 2)
    fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF:.5f}:offset={off:.5f}[x{k}]")
    prev = f"[x{k}]"
video = f"{WORK}/video.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                "-filter_complex", ";".join(fc), "-map", prev,
                "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p", video], check=True)

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", AUDIO,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", OUT], check=True)
print("done ->", OUT, flush=True)
