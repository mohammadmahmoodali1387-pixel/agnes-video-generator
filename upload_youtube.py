
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError("YouTube credentials are missing.")

    video_files = list(Path("outputs").glob("*.mp4"))

    if not video_files:
        raise FileNotFoundError("No MP4 video found in outputs folder.")

    video_path = max(video_files, key=lambda p: p.stat().st_mtime)

    title = os.environ.get(
        "YOUTUBE_TITLE",
        "Tiny Construction ASMR #Shorts"
    )

    description = os.environ.get(
        "YOUTUBE_DESCRIPTION",
        "A tiny construction project from start to finish. "
        "Relax and enjoy satisfying miniature ASMR sounds!"
    )

    tags = os.environ.get(
        "YOUTUBE_TAGS",
        "TinyBuildASMR,MiniatureConstruction,ASMR,Shorts"
    ).split(",")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    video_metadata = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": [tag.strip() for tag in tags if tag.strip()],
            "categoryId": "26"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=video_metadata,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Upload complete: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
  
