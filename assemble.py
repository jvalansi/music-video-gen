"""
Video assembly — stitches generated clips and syncs cuts to beat timestamps.
Requires ffmpeg installed.
"""
import subprocess


def concat_clips(clip_paths: list[str], output_path: str = "final.mp4") -> str:
    filelist = "filelist.txt"
    with open(filelist, "w") as f:
        for path in clip_paths:
            f.write(f"file '{path}'\n")
    subprocess.run(
        ["ffmpeg", "-f", "concat", "-safe", "0", "-i", filelist, "-c", "copy", output_path],
        check=True
    )
    return output_path


def cut_to_beats(video_path: str, beat_times: list[float], output_path: str = "synced.mp4") -> str:
    """Cuts a long video at beat timestamps and reassembles."""
    clips = []
    for i, t in enumerate(beat_times[:-1]):
        clip = f"clip_{i}.mp4"
        duration = beat_times[i + 1] - t
        subprocess.run(
            ["ffmpeg", "-ss", str(t), "-i", video_path, "-t", str(duration), "-c", "copy", clip],
            check=True
        )
        clips.append(clip)
    return concat_clips(clips, output_path)
