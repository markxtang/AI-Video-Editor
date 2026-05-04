import warnings
import whisper
import subprocess
import re
import sys
import os
import shutil

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

def detect_silences(video_path, noise_db=-30, min_duration=0.1):
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    starts = re.findall(r"silence_start: ([\d.]+)", output)
    ends = re.findall(r"silence_end: ([\d.]+)", output)
    durations = re.findall(r"silence_duration: ([\d.]+)", output)

    silences = []
    for i, start in enumerate(starts):
        silences.append({
            "start": float(start),
            "end": float(ends[i]) if i < len(ends) else None,
            "duration": float(durations[i]) if i < len(durations) else None
        })
    return silences

def find_pauses(silences, words, min_pause=0.5, max_pause=2.0):
    pauses = []
    for silence in silences:
        if silence["duration"] is None:
            continue
        if silence["duration"] < min_pause or silence["duration"] > max_pause:
            continue
        prev_word = None
        next_word = None
        for word in words:
            if word["end"] <= silence["start"]:
                prev_word = word
            if word["start"] >= silence["end"] and next_word is None:
                next_word = word
        if prev_word and next_word:
            pauses.append({
                "silence_start": silence["start"],
                "silence_end": silence["end"],
                "duration": silence["duration"],
            })
    return pauses

def find_long_words(words, threshold=2.0):
    if not words:
        return []
    durations = [w["duration"] for w in words]
    mean = sum(durations) / len(durations)
    variance = sum((d - mean) ** 2 for d in durations) / len(durations)
    stddev = variance ** 0.5
    cutoff = mean + threshold * stddev
    return [w for w in words if w["duration"] >= cutoff]

def process(video_path, noise_db=-30, min_silence=0.1, suffix=""):
    video_path = os.path.abspath(video_path)
    video_dir  = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Create project folder and subfolders
    project_dir     = os.path.join(video_dir, video_name)
    media_dir       = os.path.join(project_dir, "Media")
    transcripts_dir = os.path.join(project_dir, "Transcripts")
    export_dir      = os.path.join(project_dir, "Export")
    for d in [media_dir, transcripts_dir, export_dir]:
        os.makedirs(d, exist_ok=True)
    print(f"Project folder: {project_dir}")

    # Copy original video into Media/
    dest_video = os.path.join(media_dir, os.path.basename(video_path))
    if not os.path.exists(dest_video):
        shutil.copy2(video_path, dest_video)
        print(f"Copied video to Media/")

    transcript_base = os.path.join(transcripts_dir, video_name)
    media_base      = os.path.join(media_dir, video_name)

    # --- Whisper ---
    print("Loading Whisper model...")
    model = whisper.load_model("base")
    print(f"Transcribing...")
    result = model.transcribe(
        dest_video,
        word_timestamps=True,
        initial_prompt="Um, uh, like, you know, so, uh, um, hmm, ah, er..."
    )

    words = []
    for seg in result["segments"]:
        for word in seg["words"]:
            words.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"],
                "duration": word["end"] - word["start"]
            })

    # --- ffmpeg silence detection ---
    print("Detecting silences...")
    silences = detect_silences(dest_video, noise_db, min_silence)

    pauses = find_pauses(silences, words)
    long_words = find_long_words(words)
    long_word_starts = {w["start"] for w in long_words}

    # 1. Plain transcript
    transcript_path = transcript_base + f"{suffix}.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())

    # 2. Analysis timeline
    timeline = []
    for word in words:
        timeline.append(("word", word["start"], word))
    for p in pauses:
        timeline.append(("pause", p["silence_start"], p))
    timeline.sort(key=lambda x: x[1])

    WORD_END_BUFFER = 0.3
    analysis_path = transcript_base + f"{suffix}_analysis.txt"
    with open(analysis_path, "w", encoding="utf-8") as f:
        for kind, _, item in timeline:
            if kind == "word":
                line = f"[{item['start']:.2f}s - {item['end'] + WORD_END_BUFFER:.2f}s]  {item['word']}"
                if item["start"] in long_word_starts:
                    line += f"  << LONG WORD ({item['duration']:.2f}s)"
                f.write(line + "\n")
            else:
                f.write(
                    f"  *** PAUSE ({item['duration']:.2f}s) "
                    f"[{item['silence_start']:.2f}s - {item['silence_end']:.2f}s] ***\n"
                )

    # 3. Extract WAV audio into Media/
    wav_path = media_base + ".wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", dest_video,
        "-vn", "-acodec", "pcm_s16le", wav_path
    ], check=True, capture_output=True)

    print(f"\nTranscript:    {transcript_path}")
    print(f"Analysis:      {analysis_path}")
    print(f"WAV audio:     {wav_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py process.py <video_path> [noise_db=-30] [min_silence=0.1] [suffix]")
        sys.exit(1)

    video_path = sys.argv[1]
    noise_db = int(sys.argv[2]) if len(sys.argv) > 2 else -30
    min_silence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    suffix = sys.argv[4] if len(sys.argv) > 4 else ""

    process(video_path, noise_db, min_silence, suffix)
