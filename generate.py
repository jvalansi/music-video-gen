import os
import time
import base64
import requests

API_KEY = os.environ["OPENROUTER_API_KEY"]
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

IMAGE_PROMPT = (
    "A cyborg mermaid with bioluminescent scales and chrome mechanical fins, "
    "floating in deep dark ocean water, glowing circuitry running along her body, "
    "ethereal blue and teal light emanating from within, long flowing hair, "
    "looking upward, cinematic, photorealistic, 4K"
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
    image_data = response.json()["choices"][0]["message"]["content"][0]["image_url"]["url"]
    image_bytes = base64.b64decode(image_data.split(",")[1])
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"Image saved to {output_path}")
    return output_path


def generate_video(image_path: str, prompt: str, output_path: str = "output.mp4") -> str:
    print("Submitting video generation...")
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    response = requests.post(
        "https://openrouter.ai/api/v1/videos/generations",
        headers=HEADERS,
        json={
            "model": "bytedance/seedance-2.0",
            "prompt": prompt,
            "image": f"data:image/png;base64,{image_b64}",
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
            f"https://openrouter.ai/api/v1/videos/generations/{task_id}",
            headers=HEADERS
        ).json()
        status = result["status"]
        print(f"Status: {status}")
        if status == "completed":
            video_url = result["results"][0]["url"]
            video_data = requests.get(video_url).content
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
