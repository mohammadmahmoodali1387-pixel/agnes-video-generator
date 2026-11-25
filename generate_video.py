import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
import urllib.parse

API_KEY = os.environ.get("AGNES_API_KEY", "")
BASE_URL = "https://apihub.agnes-ai.com"
MODEL = "agnes-video-2.5-flash"

def request_json(url, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url, data=body, headers=headers, method=method
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: AGNES_API_KEY is missing")
        sys.exit(1)

    if not 4 <= args.duration <= 12:
        print("Duration must be between 4 and 12 seconds")
        sys.exit(1)

    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "mode": "text",
        "seconds": str(args.duration),
        "size": "720P",
        "aspect_ratio": "16:9",
        "n": 1
    }

    print("Submitting video request...")
    result = request_json(
        BASE_URL + "/v1/videos",
        method="POST",
        data=payload
    )

    video_id = (
        result.get("video_id")
        or result.get("task_id")
        or result.get("id")
    )

    if not video_id:
        print("No video ID returned:")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    print("Video task created:", video_id)

    for attempt in range(30):
        time.sleep(20)

        query = urllib.parse.urlencode({
            "video_id": video_id,
            "model_name": MODEL
        })

        status_result = request_json(
            BASE_URL + "/agnesapi?" + query
        )

        status = status_result.get("status", "unknown")
        print("Check", attempt + 1, "- status:", status)

        if status == "failed":
            print("Video generation failed:")
            print(json.dumps(status_result, indent=2))
            sys.exit(1)

        if status == "completed":
            video_url = (
                status_result.get("url")
                or status_result.get("video_url")
                or status_result.get("metadata", {}).get("url")
            )

            if not video_url:
                print("Video completed, but no download URL was found.")
                print(json.dumps(status_result, indent=2))
                sys.exit(1)

            os.makedirs("outputs", exist_ok=True)
            filename = "outputs/miniature_cabin_asmr.mp4"

            print("Downloading video...")
            urllib.request.urlretrieve(video_url, filename)
            print("VIDEO SAVED:", filename)
            return

    print("Timed out waiting for video.")
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as error:
        print("HTTP ERROR:", error.code)
        print(error.read().decode("utf-8", errors="ignore"))
        sys.exit(1)
    except Exception as error:
        print("ERROR:", str(error))
        sys.exit(1)
                  
