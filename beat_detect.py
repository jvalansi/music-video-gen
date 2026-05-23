"""
Beat detection — extracts timestamps for beats, drops, and sections from an audio file.
Used to sync video clip cuts to the music.
"""
import librosa
import numpy as np


def get_beat_times(audio_path: str) -> list[float]:
    y, sr = librosa.load(audio_path)
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    return librosa.frames_to_time(beat_frames, sr=sr).tolist()


def get_sections(audio_path: str, n_segments: int = 8) -> list[float]:
    """Returns timestamps of major structural changes (verse, chorus, drop, etc.)"""
    y, sr = librosa.load(audio_path)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    bounds = librosa.segment.agglomerative(chroma, n_segments)
    return librosa.frames_to_time(bounds, sr=sr).tolist()


if __name__ == "__main__":
    import sys
    audio_path = sys.argv[1]
    print("Beats:", get_beat_times(audio_path)[:10], "...")
    print("Sections:", get_sections(audio_path))
