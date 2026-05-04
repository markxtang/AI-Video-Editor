## Scripts
`analyze.py` and `export.py` live in the same folder as this file.

## Setup (first time only)
If you don't know the path to this folder, ask the user to paste it. Save it to memory as "AIVideoEditor path" so you never need to ask again. All scripts are in that folder.

## Folder structure (per project)
```
videoname/
  Media/        — original .mp4 + .wav (PCM audio) + versioned .edl files (next to WAV for Resolve)
  Transcripts/  — plain .txt + _analysis.txt
  Export/       — versioned subfolders: videoname_v1/, videoname_v2/, ...
```

Each `Export/vN/` contains:
- `videoname_vN.txt`  — notes file (written FIRST by Claude before export)
- `videoname_vN.mp4` — default export
- `videoname_vN_1080p.mp4` — with optional suffix (e.g. 1080p, 720p, vertical, 1080x1080)

## Workflow

**1. Analyze the video**
```
python "<path to this folder>/analyze.py" "path/to/video.mp4"
```
Creates project folder with subfolders, runs Whisper transcription + ffmpeg silence detection.
Outputs: `Transcripts/videoname.txt`, `Transcripts/videoname_analysis.txt`, `Media/videoname.wav`

**2. Review `_analysis.txt` and present a summary**
After analyze.py completes, read both output files and present:
1. The plain transcript text
2. Flagged items grouped by type (omit any group with nothing to report):
   - **Long words** — word, timecode, duration
   - **Pauses** — duration, timecode
   - **Filler words** — word, timecode
   - **Stumbles** — repeated words close together indicating a false start
3. Suggested cuts with timecodes and a brief reason for each
Then ask the user what they want to cut.

**3. Write the notes file**
Create `Export/videoname_vN/videoname_vN.txt` with this format:
```
Version: vN
Date: YYYY-MM-DD

Cuts:
<human-readable description of what was cut>

Scale: 1920x1080
Suffix: 1080p
Padding: 0.2  # seconds added to the end of each segment to avoid the last word getting cut off
Segments: (start1, end1), (start2, end2), ...
```
`Scale:`, `Crop:`, and `Suffix:` are optional. `Padding:` and `Segments:` are required. Always include `Padding:` with the comment exactly as shown above — use 0.2 unless the user specifies otherwise.

**4. Run export.py**
```
python "<path to this folder>/export.py" "Media/videoname.mp4" <version>
```
`export.py` reads everything from the notes file, renders via ffmpeg, generates versioned EDL into `Media/`.

**5. Import into DaVinci Resolve**
File → Import Timeline → Import AAF, EDL, XML → select `.edl` from `Media/`.
Add source video to media pool first so Resolve links correctly. WAV auto-found (same folder as EDL).

## Naming conventions
- Export subfolder: `videoname_vN/` (no suffix)
- Export file: `videoname_vN.mp4` or `videoname_vN_1080p.mp4`, `videoname_vN_vertical.mp4` etc.
- EDL: `videoname_vN.edl` in `Media/`
- Notes: `videoname_vN.txt` in `Export/vN/`
- Multiple exports of same version (same cuts, different format) go in the same `vN/` folder
- Increment version number for different cuts

## Editing decisions
**Go straight to export** when instructions map cleanly to the analysis:
- Simple removals with obvious timecode boundaries ("remove all pauses", "end at X")

**Show cut list first and wait for confirmation** when:
- 4 or more segments involved
- Instructions are ambiguous
- A judgment call is needed on a timecode boundary

## Key technical notes
- WAV (PCM) required for Resolve EDL audio — AAC causes silent first clips due to decoder priming
- `analyze.py` uses Whisper `base` model with `initial_prompt` to catch filler words (um, uh)
- Pause threshold: min 0.5s, max 2.0s
- Long word detection: flags words > 2 standard deviations above mean duration
- EDL uses separate `V` and `AA` events per clip (video from MP4, audio from WAV)
- If no Scale: is set, export.py detects source resolution via ffprobe and prompts the user to confirm or enter a custom value
