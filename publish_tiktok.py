"""
Upload a video to TikTok via the TikTok Content Posting API.

Setup:
1. Go to https://developers.tiktok.com and create an app
2. Add "Content Posting API" product and request approval
3. Generate an access token with video.publish scope
4. Set TIKTOK_ACCESS_TOKEN in .env

Note: Video must be MP4, under 4GB, 3-600 seconds.
"""
import os
import time
import requests


def upload_video(video_path: str, title: str, access_token: str) -> str:
    # Step 1: initialize upload
    print("Initializing upload...")
    file_size = os.path.getsize(video_path)
    r = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={
            "post_info": {
                "title": title,
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            }
        }
    )
    r.raise_for_status()
    data = r.json()["data"]
    publish_id = data["publish_id"]
    upload_url = data["upload_url"]
    print(f"Publish ID: {publish_id}")

    # Step 2: upload file
    print("Uploading video...")
    with open(video_path, "rb") as f:
        requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            },
            data=f
        ).raise_for_status()

    # Step 3: poll until published
    print("Waiting for publish...")
    for _ in range(30):
        status = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"publish_id": publish_id}
        ).json()["data"]["status"]
        print(f"  Status: {status}")
        if status == "PUBLISH_COMPLETE":
            print("Published!")
            return publish_id
        elif status in ("FAILED", "SPAM_DETECTED"):
            raise RuntimeError(f"Publish failed: {status}")
        time.sleep(10)

    return publish_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="final_vertical.mp4")
    parser.add_argument("--title", default="AI-generated music video 🤖🧜 #aimusic #electronic #suno")
    args = parser.parse_args()

    token = os.environ["TIKTOK_ACCESS_TOKEN"]
    upload_video(args.video, args.title, token)
