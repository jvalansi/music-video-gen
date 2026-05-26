"""
Upload a video to YouTube via the YouTube Data API v3.

Setup:
1. Go to https://console.cloud.google.com
2. Create a project, enable "YouTube Data API v3"
3. Create OAuth 2.0 credentials (Desktop app) and download as client_secrets.json
4. pip install google-auth google-auth-oauthlib google-api-python-client
5. Run this script — it will open a browser for auth on first run, then save token.json
"""
import os
import argparse
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRETS = "client_secrets.json"
TOKEN_FILE = "token.json"


def get_youtube_client():
    import google.oauth2.credentials
    from google.auth.transport.requests import Request

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, title: str, description: str = "", tags: list[str] = None, category_id: str = "10"):
    youtube = get_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,  # 10 = Music
        },
        "status": {
            "privacyStatus": "public",
        }
    }

    print(f"Uploading {video_path}...")
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Done! https://www.youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="final_youtube.mp4")
    parser.add_argument("--title", default="Robot Mermaid — AI Music Video")
    parser.add_argument("--description", default="AI-generated music video made with Seedance 2.0 & OpenRouter.")
    parser.add_argument("--tags", default="ai music,electronic,suno,ai video")
    parser.add_argument("--whoami", action="store_true", help="Print the authenticated channel and exit")
    args = parser.parse_args()

    if args.whoami:
        youtube = get_youtube_client()
        resp = youtube.channels().list(part="snippet", mine=True).execute()
        for ch in resp.get("items", []):
            print(f"{ch['id']}  {ch['snippet']['title']}")
    else:
        upload_video(args.video, args.title, args.description, args.tags.split(","))
