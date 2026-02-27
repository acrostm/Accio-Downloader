import time
import re
import pyperclip
import requests
import argparse

# Bilibili, Douyin, TikTok, X (Twitter) simple regexes
SUPPORTED_DOMAINS_PATTERN = re.compile(r'(bilibili\.com|douyin\.com|tiktok\.com|x\.com|twitter\.com)')
URL_PATTERN = re.compile(r'(https?://[^\s]+)')

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

def extract_url(text):
    match = URL_PATTERN.search(text)
    if match:
        return match.group(1)
    return None

def is_supported(url):
    return bool(SUPPORTED_DOMAINS_PATTERN.search(url))

def main():
    parser = argparse.ArgumentParser(description="Accio PC Clipboard Watcher")
    parser.add_argument("--action", type=str, choices=["local", "webdav"], default="webdav", help="Target action for downloads")
    args = parser.parse_args()

    print("Starting PC Clipboard Watcher for Accio-Downloader...")
    print(f"Action configured: {args.action}")
    print("Listening for Bilibili, Douyin, TikTok, and X links...")
    
    last_processed_url = ""

    while True:
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard:
                url = extract_url(current_clipboard)
                
                # Check if it's a valid and supported URL we haven't seen yet
                if url and url != last_processed_url and is_supported(url):
                    print(f"\n[+] Detected supported URL: {url}")
                    
                    try:
                        # Send download start request directly
                        download_url = f"{API_BASE_URL}/video/download"
                        payload = {"url": url, "action": args.action, "format_id": "best"}
                        print(f"[*] Dispatching background download task to {download_url}...")
                        response = requests.post(download_url, json=payload, timeout=15)
                        
                        if response.status_code == 200:
                            data = response.json()
                            print(f"[Success] Task submitted successfully! Task ID: {data.get('task_id')}")
                            # Update last processed on success to avoid infinite loop
                            last_processed_url = url
                        else:
                            print(f"[Error] Failed to initiate task. Status: {response.status_code}, Msg: {response.text}")
                    except requests.RequestException as e:
                        print(f"[Error] Could not reach backend API: {e}")

            time.sleep(1)
            
        except pyperclip.PyperclipException as e:
            print(f"Clipboard read error: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
