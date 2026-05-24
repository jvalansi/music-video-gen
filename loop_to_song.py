"""
Loop a video clip to match the duration of an audio file, then mux the audio in.
Usage: python loop_to_song.py <song_file> [--video output_loop.mp4] [--out final.mp4]
"""
import argparse
import subprocess


def get_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())


def loop_video_to_song(song_path: str, video_path: str = "output_loop.mp4", output_path: str = "final.mp4"):
    song_duration = get_duration(song_path)
    print(f"Song duration: {song_duration:.2f}s")

    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", video_path,
        "-i", song_path,
        "-t", str(song_duration),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        output_path
    ], check=True)

    print(f"Saved {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("song", help="Path to audio file (mp3, wav, etc.)")
    parser.add_argument("--video", default="output_loop.mp4", help="Video clip to loop")
    parser.add_argument("--out", default="final.mp4", help="Output file")
    args = parser.parse_args()
    loop_video_to_song(args.song, args.video, args.out)
