# AIVideoEditor

AI-assisted video editing pipeline. Transcribes video with Whisper, detects pauses and filler words, then exports trimmed clips via ffmpeg with DaVinci Resolve-compatible EDLs.

## Dependencies

**System:** [ffmpeg](https://ffmpeg.org/download.html) (must be in PATH)

**Python:** [openai-whisper](https://github.com/openai/whisper)
```
pip install -r requirements.txt
```

**AI:** [Claude Code](https://claude.ai/code) — the workflow is designed to be driven by Claude Code, which reads the analysis output, decides what to cut, writes the notes file, and runs the export.

## Usage

### 1. Analyze
```
python analyze.py "path/to/video.mp4"
```

Creates a project folder next to the video:
```
videoname/
  Media/        — copy of original .mp4 + .wav (PCM audio) + EDL files
  Transcripts/  — videoname.txt (plain) + videoname_analysis.txt (timestamped)
  Export/       — versioned export subfolders
```

The analysis file flags pauses, long words, and filler words (um, uh) with timestamps.

### 2. Write a notes file

Create `Export/videoname_v1/videoname_v1.txt`:
```
Version: v1
Date: YYYY-MM-DD

Cuts:
Description of what was removed

Segments: (0.00, 4.50), (6.20, 12.00)
```

Optional fields:
- `Scale: 1920x1080` — output resolution (defaults to source resolution if omitted)
- `Crop: 2088x2088` — crop before scaling (center crop)
- `Suffix: 1080p` — appended to output filename

### 3. Export
```
python export.py "Media/videoname.mp4" 1
```

Pass the version as a number (`1`, `2`, etc.). Outputs:
- `Export/videoname_v1/videoname_v1.mp4` (or with suffix)
- `Media/videoname_v1.edl` — for import into DaVinci Resolve

### 4. Import EDL into DaVinci Resolve (optional)

File → Import Timeline → Import AAF, EDL, XML → select the `.edl` from `Media/`.
Add the source video to the media pool first so Resolve can link it. The WAV is auto-detected (same folder as EDL).

## Notes

- Whisper runs on CPU by default (FP32). A CUDA-capable GPU will speed up transcription significantly.
- WAV (PCM) is required for Resolve EDL audio — AAC causes a silent first clip due to decoder priming.
- Multiple exports of the same version (same cuts, different formats) go in the same `vN/` folder. Increment the version number for different cuts.
