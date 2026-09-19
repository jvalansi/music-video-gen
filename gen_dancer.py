import os
from generate import generate_image, generate_video

IMAGE_PROMPT = (
    "Backlit silhouette of a dancing girl in a wide empty warehouse at golden hour, "
    "face and features hidden in shadow, flowing dress and long hair swirling mid-motion, "
    "thick volumetric sunbeams through tall windows, drifting dust particles, "
    "warm amber and soft teal palette, painterly illustrated style, dreamy and ethereal, "
    "cinematic wide shot, film grain, 4K"
)

VIDEO_PROMPT = (
    "She dances fluidly, spinning and swaying, dress and hair flowing with the movement, "
    "dust motes drifting through the light beams, slow subtle camera push-in, "
    "smooth continuous motion, no cuts"
)

if __name__ == "__main__":
    img = generate_image(IMAGE_PROMPT, "dancer.png")
    generate_video(img, VIDEO_PROMPT, "dancer.mp4", loop=False)
