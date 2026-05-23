# music-video-gen

AI music video generator — beat-synced video generation from audio using Seedance & OpenRouter.

## Vision

Generate videos that are automatically adjusted to the music: beat detection → scene generation → video assembly synced to drops and transitions.

## Setup

```bash
cp .env.example .env
# add your OpenRouter API key to .env
pip install requests librosa
```

## Usage

```bash
# Generate image + video for a prompt
python generate.py

# Detect beats in an audio file
python beat_detect.py your_song.mp3

# Assemble clips synced to beats (coming soon)
python assemble.py
```

## Pipeline

1. **`generate.py`** — text prompt → image (GPT-5.4 Image) → video (Seedance 2.0)
2. **`beat_detect.py`** — audio → beat/section timestamps via librosa
3. **`assemble.py`** — stitch clips with cuts at beat timestamps via ffmpeg
4. **`prompts.py`** — prompt library keyed by mood/style
