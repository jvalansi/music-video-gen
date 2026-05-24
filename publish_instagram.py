"""
Upload a video to Instagram Reels via the Instagram Graph API.

Setup:
1. Go to https://developers.facebook.com and create an app (type: Business)
2. Add "Instagram Graph API" product
3. Link your Instagram Business/Creator account to a Facebook Page
4. Generate a long-lived access token (User Token with instagram_basic,
   instagram_content_publish scopes) via Graph API Explorer
5. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID in .env

Note: Video must be 9:16, 1080x1920, under 1GB, 3-90 seconds.
"""
import os
import time
import requests


def upload_reel(video_path: str, caption: str, access_token: str, user_id: str) -> str:
    # Step 1: upload video to get container ID
    print("Creating media container...")
    r = requests.post(
        f"https://graph.instagram.com/v21.0/{user_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_path,  # must be a public URL
            "caption": caption,
            "access_token": access_token,
        }
    )
    r.raise_for_status()
    container_id = r.json()["id"]
    print(f"Container ID: {container_id}")

    # Step 2: wait for container to finish processing
    print("Waiting for processing...")
    for _ in range(30):
        status = requests.get(
            f"https://graph.instagram.com/v21.0/{container_id}",
            params={"fields": "status_code", "access_token": access_token}
        ).json().get("status_code")
        print(f"  Status: {status}")
        if status == "FINISHED":
            break
        elif status == "ERROR":
            raise RuntimeError("Container processing failed")
        time.sleep(10)

    # Step 3: publish
    print("Publishing...")
    r = requests.post(
        f"https://graph.instagram.com/v21.0/{user_id}/media_publish",
        params={"creation_id": container_id, "access_token": access_token}
    )
    r.raise_for_status()
    media_id = r.json()["id"]
    print(f"Published! Media ID: {media_id}")
    return media_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-url", required=True, help="Public URL of the video (e.g. GitHub raw URL)")
    parser.add_argument("--caption", default="AI-generated music video 🤖🧜 #aimusic #electronic #suno")
    args = parser.parse_args()

    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]
    upload_reel(args.video_url, args.caption, token, user_id)
