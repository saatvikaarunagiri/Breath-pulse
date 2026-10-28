# Voice model goes here (optional)

Voice features (speaking to the app + the assistant replying out loud) use an
**offline** Vosk model so nothing leaves your computer.

**Easiest:** from the project folder run `python download_model.py`.

**Manual:** download the small English model
(`vosk-model-small-en-us-0.15.zip`, ~40 MB) from
https://alphacephei.com/vosk/models/ , unzip it, rename the folder to
`vosk-model-small-en-us`, and place it in this `models/` folder.

Skip all of this if you don't want voice — the apps run fine without it.
