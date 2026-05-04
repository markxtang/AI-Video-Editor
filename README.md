# AI Video Editor

A video editing pipeline that uses AI to transcribe your footage, identify problem areas, and export trimmed clips. The workflow is designed to be run through Claude Code — you describe what you want cut, and Claude handles the timecodes, the notes file, and the export commands.

## What you need

**[ffmpeg](https://ffmpeg.org/download.html)** — a command-line tool that processes and exports video.

**[openai-whisper](https://github.com/openai/whisper)** — a speech-to-text model that transcribes your video locally on your machine. Install it by running:
```
pip install -r requirements.txt
```

**[Claude Code](https://claude.ai/code)** — the workflow is designed to be driven by Claude Code, which reads the analysis output, decides what to cut, writes the notes file, and runs the export.

## Getting started

1. Download or clone this repository to your machine.
2. Install the dependencies listed above.
3. Open Claude Code and set the working directory to the folder where you downloaded the repo. Claude Code automatically reads the `CLAUDE.md` file in that folder, which contains the full workflow instructions. Alternatively, you can paste the path to `CLAUDE.md` directly into Claude and ask it to read the file.

Once that's done, you're ready to start editing.

## How to use it

### 1. Analyze your video

Tell Claude the path to your video file and ask it to analyze it. Claude runs `analyze.py`, which does two things: transcribes the audio using Whisper, and scans for silences using ffmpeg. It creates a project folder next to your video with this structure:

```
videoname/
  Media/        — copy of your original video + a WAV audio file
  Transcripts/  — plain transcript + a timestamped analysis file
  Export/       — where finished exports are saved
```

The analysis file lists every word with its start and end time, and flags pauses, filler words (um, uh), and unusually long words.

### 2. Tell Claude what to cut

Read through the transcript and tell Claude what you want removed — you can reference specific words, sentences, or time ranges. Claude identifies the exact timecodes, creates a notes file in the Export folder, and runs the export.

The notes file looks like this:
```
Version: v1
Date: YYYY-MM-DD

Cuts:
Description of what was removed

Segments: (0.00, 4.50), (6.20, 12.00)
```

`Segments` is the only required field. Each pair of numbers is a start and end time (in seconds) of footage to keep. Optional fields:
- `Scale: 1920x1080` — output resolution. Claude will ask if you don't specify.
- `Crop: 2088x2088` — crops the frame before scaling, from the center.
- `Suffix: 1080p` — added to the output filename (e.g. `videoname_v1_1080p.mp4`).

### 3. Review the export

Finished videos are saved to `Export/videoname_v1/`. Each new set of cuts gets a new version number, so previous exports are never overwritten. Multiple formats of the same cut (e.g. 1080p and square) go in the same version folder.

### 4. Import into DaVinci Resolve (optional)

The export also generates an EDL file — a standard format that video editing software uses to represent a cut timeline. To import it into DaVinci Resolve: add your source video to the media pool first, then go to File → Import Timeline → Import AAF, EDL, XML and select the `.edl` file from your `Media/` folder.

## Notes

- Transcription runs on your CPU by default, which is slower. If your machine has a compatible GPU, Whisper will use it automatically and run significantly faster.
- The WAV file in `Media/` is used for the Resolve EDL — Resolve has a known issue with AAC audio in EDL imports that causes the first clip to be silent. The WAV avoids this.
