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

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS = "client_secrets.json"
TOKEN_FILE = "token.json"


def get_youtube_client():
    import json
    import google.oauth2.credentials
    from google.auth.transport.requests import Request

    with open(CLIENT_SECRETS) as f:
        secrets = json.load(f)["installed"]

    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        token_data.setdefault("client_id", secrets["client_id"])
        token_data.setdefault("client_secret", secrets["client_secret"])
        creds = google.oauth2.credentials.Credentials.from_authorized_user_info(token_data, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            print("Token missing or expired. Re-authenticate:")
            print("  python publish_youtube.py --get-auth-url")
            print("  python publish_youtube.py --complete-auth 'http://localhost/?code=...'")
            raise SystemExit(1)
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


VERIFIER_FILE = ".auth_verifier"


def get_auth_url():
    import json
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS, scopes=SCOPES, redirect_uri="http://localhost"
    )
    auth_url, _ = flow.authorization_url(prompt="select_account", access_type="offline")
    with open(CLIENT_SECRETS) as f:
        secrets = json.load(f)["installed"]
    with open(VERIFIER_FILE, "w") as f:
        import json as _json
        _json.dump({"verifier": flow.code_verifier, "client_id": secrets["client_id"], "client_secret": secrets["client_secret"]}, f)
    print(auth_url)


def complete_auth(redirect_url: str):
    import json, urllib.parse, requests as _requests
    with open(VERIFIER_FILE) as f:
        saved = json.load(f)
    code = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query)["code"][0]
    r = _requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": saved["client_id"],
        "client_secret": saved["client_secret"],
        "redirect_uri": "http://localhost",
        "grant_type": "authorization_code",
        "code_verifier": saved["verifier"],
    })
    r.raise_for_status()
    token = r.json()
    token["client_id"] = saved["client_id"]
    token["client_secret"] = saved["client_secret"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)
    os.remove(VERIFIER_FILE)
    print("Authenticated. Run --whoami to verify.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="final_youtube.mp4")
    parser.add_argument("--title", default="Robot Mermaid — AI Music Video")
    parser.add_argument("--description", default="AI-generated music video made with Seedance 2.0 & OpenRouter.")
    parser.add_argument("--tags", default="ai music,electronic,suno,ai video")
    parser.add_argument("--whoami", action="store_true", help="Print the authenticated channel and exit")
    parser.add_argument("--get-auth-url", action="store_true", help="Print the OAuth URL and save verifier")
    parser.add_argument("--complete-auth", metavar="REDIRECT_URL", help="Complete OAuth with the redirect URL")
    args = parser.parse_args()

    if args.get_auth_url:
        get_auth_url()
    elif args.complete_auth:
        complete_auth(args.complete_auth)
    elif args.whoami:
        youtube = get_youtube_client()
        resp = youtube.channels().list(part="snippet", mine=True).execute()
        for ch in resp.get("items", []):
            print(f"{ch['id']}  {ch['snippet']['title']}")
    else:
        upload_video(args.video, args.title, args.description, args.tags.split(","))
