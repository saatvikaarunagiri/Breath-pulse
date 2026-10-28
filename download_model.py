"""
One-time downloader for the offline voice model (Vosk small English, ~40 MB).
Only needed if you want the voice features. Run:  python download_model.py
Everything stays on your computer.
"""
import io, os, sys, urllib.request, zipfile

URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
FINAL = os.path.join(DEST, "vosk-model-small-en-us")

def main():
    if os.path.isdir(FINAL):
        print("Model already present at", FINAL)
        return
    os.makedirs(DEST, exist_ok=True)
    print("Downloading ~40 MB voice model… (one time)")
    try:
        data = urllib.request.urlopen(URL, timeout=60).read()
    except Exception as e:
        print("Download failed:", e)
        print("You can download it manually from:", URL)
        print("Unzip it, then rename the folder to 'vosk-model-small-en-us'")
        print("and place it inside:", DEST)
        sys.exit(1)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(DEST)
    # the zip extracts as vosk-model-small-en-us-0.15 -> rename
    extracted = os.path.join(DEST, "vosk-model-small-en-us-0.15")
    if os.path.isdir(extracted):
        os.rename(extracted, FINAL)
    print("Done! Voice model ready at", FINAL)

if __name__ == "__main__":
    main()
