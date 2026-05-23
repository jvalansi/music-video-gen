import os
import time
import base64
import requests

# base64 used only for decoding image response from OpenRouter

API_KEY = os.environ["OPENROUTER_API_KEY"]
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

IMAGE_PROMPT = (
    "A futuristic humanoid robot with bioluminescent aquatic armor and chrome fins, "
    "submerged in deep dark ocean water, glowing blue circuitry running along its body, "
    "ethereal teal light emanating from within, long flowing metallic tendrils, "
    "looking upward toward the surface, cinematic sci-fi, photorealistic, 4K"
)

VIDEO_PROMPT = (
    "Slow underwater drift, hair and fins gently moving with the current, "
    "bioluminescent lights pulsing rhythmically, bubbles rising"
)


def generate_image(prompt: str, output_path: str = "frame.png") -> str:
    print("Generating image...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": "openai/gpt-5.4-image-2",
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image"]
        }
    )
    response.raise_for_status()
    image_data = response.json()["choices"][0]["message"]["images"][0]["image_url"]["url"]
    image_bytes = base64.b64decode(image_data.split(",")[1])
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"Image saved to {output_path}")
    return output_path


def upload_image(image_path: str) -> str:
    """Push image to GitHub and return raw content URL."""
    import subprocess
    print("Uploading image via GitHub...")
    repo_dir = os.path.dirname(os.path.abspath(image_path))
    filename = os.path.basename(image_path)
    subprocess.run(["git", "-C", repo_dir, "add", "-f", image_path], check=True)
    subprocess.run(["git", "-C", repo_dir, "commit", "--allow-empty", "-m", f"upload {filename}"], check=True)
    subprocess.run(["git", "-C", repo_dir, "push"], check=True)
    url = f"https://raw.githubusercontent.com/jvalansi/music-video-gen/main/{filename}"
    print(f"Image URL: {url}")
    return url


def generate_video(image_path: str, prompt: str, output_path: str = "output.mp4") -> str:
    print("Submitting video generation...")
    image_url = upload_image(image_path)

    response = requests.post(
        "https://openrouter.ai/api/v1/videos",
        headers=HEADERS,
        json={
            "model": "bytedance/seedance-2.0",
            "prompt": prompt,
            "frame_images": [{"type": "image_url", "image_url": {"url": image_url}, "frame_type": "first_frame"}],
            "duration": 10,
            "resolution": "1080p"
        }
    )
    response.raise_for_status()
    task_id = response.json()["id"]
    print(f"Task ID: {task_id}")

    print("Waiting for video...")
    while True:
        result = requests.get(
            f"https://openrouter.ai/api/v1/videos/{task_id}",
            headers=HEADERS
        ).json()
        status = result["status"]
        print(f"Status: {status}")
        if status == "completed":
            video_content_url = result["unsigned_urls"][0]
            video_data = requests.get(video_content_url, headers=HEADERS).content
            with open(output_path, "wb") as f:
                f.write(video_data)
            print(f"Video saved to {output_path}")
            return output_path
        elif status == "failed":
            raise RuntimeError(f"Generation failed: {result}")
        time.sleep(10)


if __name__ == "__main__":
    image_path = generate_image(IMAGE_PROMPT)
    generate_video(image_path, VIDEO_PROMPT)
