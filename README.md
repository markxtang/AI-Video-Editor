# AI Video Editor

Record your video, then tell Claude what to cut — in plain English. Claude listens to what you said, spots the pauses and stumbles, and exports a clean version automatically.

## What you need

**[ffmpeg](https://ffmpeg.org/download.html)** — the tool that actually cuts and exports the video. Free to download.

**[openai-whisper](https://github.com/openai/whisper)** — the AI that transcribes your video so Claude can read what you said.

**[Claude Code](https://claude.ai/code)** — the workflow is designed to be driven by Claude Code, which reads the analysis output, decides what to cut, writes the notes file, and runs the export.

Once ffmpeg and Claude Code are installed, run this once to set up Whisper:
```
pip install -r requirements.txt
```

## How it works

### 1. Analyze your video

Give Claude the path to your video file and ask it to analyze it. Claude will run the analysis and show you a transcript with timestamps, flagging pauses, filler words (um, uh), and any stumbles.

### 2. Tell Claude what to cut

Just describe what you want removed in plain English — "cut the pause at the end", "remove that whole sentence", "end the video after I say X". Claude figures out the exact timestamps and prepares the export.

### 3. Choose your export settings

Claude will ask what resolution you want. You can say things like "1080p", "square for Instagram", or "same as the original". It handles the rest.

### 4. Get your video

Claude exports the finished video into an `Export/` folder next to your original. Each version is numbered so nothing gets overwritten — you can always go back to a previous cut.

### 5. Import into DaVinci Resolve (optional)

If you edit in DaVinci Resolve, Claude also generates a timeline file you can import directly — so you can do color grading or audio work on top of the cuts.

## Tips

- The longer the video, the longer the initial analysis takes — Whisper is running on your CPU.
- You can do multiple rounds of cuts without re-analyzing. Just tell Claude what else to change and it'll export a new version.
- If you want the same cuts at a different size (say, both 1080p and square), Claude can export both into the same version folder without incrementing the version number.
