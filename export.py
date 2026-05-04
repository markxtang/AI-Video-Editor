import sys
import os
import re
import subprocess
from datetime import date

def seconds_to_tc(seconds, fps=30):
    total_frames = round(seconds * fps)
    f = total_frames % fps
    total_secs = total_frames // fps
    s = total_secs % 60
    m = (total_secs // 60) % 60
    h = total_secs // 3600
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

def generate_edl(video_path, segments, fps=30):
    clip_name   = os.path.basename(video_path)
    wav_name    = os.path.splitext(clip_name)[0] + ".wav"
    title       = os.path.splitext(clip_name)[0]
    output_path = os.path.splitext(video_path)[0] + ".edl"
    tc_offset   = get_timecode_offset(video_path)

    lines = [f"TITLE: {title}", "FCM: NON-DROP FRAME", ""]
    record_time = 0.0
    for i, (src_in, src_out) in enumerate(segments, 1):
        duration = src_out - src_in
        rec_in   = record_time
        rec_out  = record_time + duration
        lines.append(f"{i:03d}  001      V     C        {seconds_to_tc(src_in + tc_offset, fps)} {seconds_to_tc(src_out + tc_offset, fps)} {seconds_to_tc(rec_in, fps)} {seconds_to_tc(rec_out, fps)}")
        lines.append(f"* FROM CLIP NAME: {clip_name}")
        lines.append(f"{i:03d}  002      AA    C        {seconds_to_tc(src_in + tc_offset, fps)} {seconds_to_tc(src_out + tc_offset, fps)} {seconds_to_tc(rec_in, fps)} {seconds_to_tc(rec_out, fps)}")
        lines.append(f"* FROM CLIP NAME: {wav_name}")
        lines.append("")
        record_time = rec_out

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"EDL saved to: {output_path}")

def read_notes(notes_path):
    segments = []
    scale    = None
    crop     = None
    suffix   = ""
    padding  = 0.2

    with open(notes_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Segments:"):
                pairs = re.findall(r'\((\d+\.?\d*),\s*(\d+\.?\d*)\)', line)
                segments = [(float(a), float(b)) for a, b in pairs]
            elif line.startswith("Scale:"):
                w, h = line.split(":", 1)[1].strip().split("x")
                scale = (int(w), int(h))
            elif line.startswith("Crop:"):
                w, h = line.split(":", 1)[1].strip().split("x")
                crop = (int(w), int(h))
            elif line.startswith("Suffix:"):
                suffix = line.split(":", 1)[1].strip()
            elif line.startswith("Padding:"):
                padding = float(line.split(":", 1)[1].strip())

    if not segments:
        raise ValueError(f"No segments found in {notes_path}")
    segments = [(s, e + padding) for s, e in segments]
    return segments, scale, crop, suffix

def get_timecode_offset(video_path):
    for scope in ["stream_tags=timecode", "format_tags=timecode"]:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", scope,
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True
        )
        tc = result.stdout.strip()
        if tc:
            h, m, s, f = map(int, tc.split(":"))
            return h * 3600 + m * 60 + s + f / 30.0
    return 0.0

def get_source_resolution(video_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", video_path],
        capture_output=True, text=True, check=True
    )
    w, h = result.stdout.strip().split(",")
    return (int(w), int(h))

def build_filter_complex(segments, scale=None, crop=None):
    parts = []
    n = len(segments)

    for i, (s, e) in enumerate(segments):
        parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}]")

    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(n))
    parts.append(f"{concat_inputs}concat=n={n}:v=1:a=1[cv][ca]")

    last_v = "cv"

    if crop:
        cw, ch = crop
        parts.append(f"[{last_v}]crop={cw}:{ch}[cropped]")
        last_v = "cropped"

    if scale:
        sw, sh = scale
        parts.append(f"[{last_v}]scale={sw}:{sh}:force_original_aspect_ratio=decrease,pad={sw}:{sh}:(ow-iw)/2:(oh-ih)/2[scaled]")
        last_v = "scaled"

    return ";".join(parts), last_v

def export(media_video_path, version):
    media_video_path = os.path.abspath(media_video_path)
    video_name  = os.path.splitext(os.path.basename(media_video_path))[0]
    media_dir   = os.path.dirname(media_video_path)
    project_dir = os.path.dirname(media_dir)

    version_name = f"{video_name}_v{version}"
    export_dir   = os.path.join(project_dir, "Export", version_name)
    os.makedirs(export_dir, exist_ok=True)

    # Read everything from the notes file
    notes_path = os.path.join(export_dir, version_name + ".txt")
    segments, scale, crop, suffix = read_notes(notes_path)

    if scale is None:
        detected = get_source_resolution(media_video_path)
        response = input(f"No Scale: set. Export at source resolution {detected[0]}x{detected[1]}? Press Enter to confirm or type custom (e.g. 1920x1080): ").strip()
        if response:
            w, h = response.split("x")
            scale = (int(w), int(h))
        else:
            scale = detected

    # Run ffmpeg
    file_suffix = f"_{suffix}" if suffix else ""
    output_path = os.path.join(export_dir, f"{version_name}{file_suffix}.mp4")
    filter_complex, v_out = build_filter_complex(segments, scale, crop)
    subprocess.run([
        "ffmpeg", "-i", media_video_path,
        "-filter_complex", filter_complex,
        "-map", f"[{v_out}]",
        "-map", "[ca]",
        output_path
    ], check=True)
    print(f"Video:        {output_path}")

    # Generate EDL into Media/ with versioned name
    generate_edl(media_video_path, segments)
    edl_src = os.path.splitext(media_video_path)[0] + ".edl"
    edl_dst = os.path.join(media_dir, version_name + ".edl")
    os.replace(edl_src, edl_dst)
    print(f"EDL:          {edl_dst}")

    print(f"Export folder: {export_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: py export.py <Media/videoname.mp4> <version>")
        print("Write Export/videoname_vN/videoname_vN.txt first with Segments, Scale, Suffix.")
        sys.exit(1)

    export(sys.argv[1], sys.argv[2])
