#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import re
import tempfile
import shutil
import subprocess
from pathlib import Path
try:
    from PIL import ImageFont
except ImportError:
    print("Error: The 'Pillow' library is required. Please install it with 'pip install Pillow'", file=sys.stderr)
    sys.exit(1)

def check_command_exists(command):
    """Check if a command exists on the system."""
    if not shutil.which(command):
        print(f"Error: '{command}' is not installed or not in your PATH.", file=sys.stderr)
        print("Please install it to continue.", file=sys.stderr)
        sys.exit(1)

def segment_text(file_path):
    """
    Reads a text file and splits it into scenes based on blank lines.
    """
    try:
        text = Path(file_path).read_text()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{file_path}'", file=sys.stderr)
        sys.exit(1)
    scenes = re.split(r'\n\s*\n', text.strip())
    validated_scenes = [scene.strip() for scene in scenes if scene.strip()]
    if not validated_scenes:
        print("Error: No valid scenes found in input file.", file=sys.stderr)
        sys.exit(1)
    return validated_scenes

def generate_audio(scene_text, temp_dir, scene_num, voice=None):
    """
    Generates a narrated audio file for a scene using macOS 'say' command.
    Automatically selects a Chinese voice if Chinese text is detected and no voice is specified.
    """
    audio_file_aiff = temp_dir / f"scene_{scene_num}.aiff"
    audio_file_m4a = temp_dir / f"scene_{scene_num}.m4a"
    text_file = temp_dir / f"scene_{scene_num}_text.txt"
    text_file.write_text(scene_text, encoding='utf-8')

    # Detect Chinese characters and select a default voice if needed
    voice_to_use = voice
    if not voice_to_use:
        # Simple check for CJK Unified Ideographs
        if any("\u4e00" <= char <= "\u9fff" for char in scene_text):
            print("  - Chinese text detected. Using 'Ting-Ting' voice.")
            voice_to_use = "Ting-Ting"

    cmd_say = ["say", "-o", str(audio_file_aiff), "-f", str(text_file)]
    if voice_to_use:
        cmd_say.extend(["-v", voice_to_use])
    
    try:
        subprocess.run(cmd_say, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio for scene {scene_num} with 'say':", file=sys.stderr)
        print(e.stderr.decode(), file=sys.stderr)
        # Check if the voice is available
        if "voice not found" in e.stderr.decode().lower():
            print(f"\nHint: The voice '{voice_to_use}' was not found on your system.", file=sys.stderr)
            print("You can list available voices with: say -v '?'", file=sys.stderr)
        raise

    cmd_ffmpeg = ["ffmpeg", "-y", "-i", str(audio_file_aiff), "-c:a", "aac", "-b:a", "192k", str(audio_file_m4a)]
    subprocess.run(cmd_ffmpeg, check=True, capture_output=True)

    cmd_ffprobe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file_m4a)]
    result = subprocess.run(cmd_ffprobe, check=True, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    return audio_file_m4a, duration



def wrap_text(text, font_file, font_size, max_width):
    """
    Wraps text to fit within a specified width.
    """
    try:
        font = ImageFont.truetype(font_file, font_size) if font_file else ImageFont.load_default()
    except IOError:
        font = ImageFont.load_default()

    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.getbbox(test_line)[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return "\n".join(lines)

def generate_video_segment(scene_data, args, temp_dir, wrapped_text, font_file):
    """
    Generates a video segment for a single scene.
    """
    scene_num = scene_data["scene_num"]
    duration = scene_data["duration"]
    audio_path = scene_data["audio_path"]
    video_path = temp_dir / f"scene_{scene_num}.mp4"

    margin = 100
    escaped_text = wrapped_text.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%")
    
    font_arg = ""
    if font_file:
        resolved_path = Path(font_file).resolve()
        ffmpeg_font_path = str(resolved_path).replace("\\", "/").replace(":", "\\:")
        font_arg = f"fontfile='{ffmpeg_font_path}':"

    drawtext_filter = (
        f"drawtext={font_arg}text='{escaped_text}':"
        f"fontsize={args.font_size}:fontcolor=white:x={margin}:y={margin}:"
        f"box=1:boxcolor=black@0.0:boxborderw=20"
    )

    cmd_ffmpeg = []
    if args.bg_image:
        cmd_ffmpeg.extend(["-loop", "1", "-i", str(Path(args.bg_image).resolve())])
    else:
        cmd_ffmpeg.extend(["-f", "lavfi", "-i", f"color=c={args.bg_color}:s={args.resolution}"])

    cmd_ffmpeg.extend([
        "-i", str(audio_path),
        "-vf", drawtext_filter,
        "-t", str(duration),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(video_path)
    ])
    
    final_cmd = ["ffmpeg", "-y"] + cmd_ffmpeg
    subprocess.run(final_cmd, check=True, capture_output=True)
    return video_path

def resplit_long_scenes(scenes, font_file, args):
    """
    Takes a list of scenes and splits any that are too long into smaller sub-scenes.
    """
    try:
        font = ImageFont.truetype(font_file, args.font_size) if font_file else ImageFont.load_default()
    except IOError:
        font = ImageFont.load_default()

    video_w, video_h = map(int, args.resolution.split('x'))
    margin = 100
    max_width = video_w - (2 * margin)
    max_height = video_h - (2 * margin)
    
    line_height = sum(font.getmetrics())
    if line_height == 0:
        return scenes
    max_lines = max_height // line_height

    final_scenes = []
    for scene_text in scenes:
        words = scene_text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.getbbox(test_line)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        if len(lines) <= max_lines:
            final_scenes.append(scene_text)
        else:
            current_chunk = []
            for i, line in enumerate(lines):
                current_chunk.append(line)
                if (i + 1) % max_lines == 0:
                    final_scenes.append(" ".join(current_chunk))
                    current_chunk = []
            if current_chunk:
                final_scenes.append(" ".join(current_chunk))
                
    return final_scenes

def concatenate_videos(video_paths, output_file, temp_dir):
    """
    Concatenates multiple video files into a single file using ffmpeg.
    """
    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w") as f:
        for path in video_paths:
            escaped_path = str(path).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path), "-c", "copy", str(Path(output_file).resolve())]
    subprocess.run(cmd, check=True, capture_output=True)

def main():
    """Main function to run the txt2video conversion."""
    parser = argparse.ArgumentParser(description="Converts a plain text file into a narrated video.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_file", nargs="?", help="Path to the input text file.")
    parser.add_argument("--output", default="output.mp4", help="Specify the output video file name.\n(default: output.mp4)")
    parser.add_argument("--resolution", default="1920x1080", help="Set the video resolution (WxH).\n(default: 1920x1080)")
    parser.add_argument("--bg-color", default="black", help="Set the video background color.\n(default: black)")
    parser.add_argument("--bg-image", help="Path to an image for the background (overrides --bg-color).")
    parser.add_argument("--voice", help="Set the TTS voice (system dependent).")
    parser.add_argument("--font-file", help="Path to a .ttf or .ttc font file.")
    parser.add_argument("--font-size", type=int, default=36, help="Set the font size.\n(default: 36)")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    if not args.input_file:
        print("Error: input_file is a required argument.", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)

    check_command_exists("say")
    check_command_exists("ffmpeg")
    check_command_exists("ffprobe")

    initial_scenes = segment_text(args.input_file)
    
    font_file = args.font_file
    if not (font_file and Path(font_file).exists()):
        if font_file:
            print(f"Warning: Font file '{font_file}' not found.", file=sys.stderr)
        if sys.platform == "darwin":
            font_file = "/System/Library/Fonts/Helvetica.ttc"
        elif sys.platform == "linux":
            font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        if not (font_file and Path(font_file).exists()):
            font_file = None
            print("Warning: Could not find a default system font.", file=sys.stderr)
    if font_file:
        print(f"Using font: {font_file}")

    final_scenes = resplit_long_scenes(initial_scenes, font_file, args)
    if len(final_scenes) > len(initial_scenes):
        print(f"Long scenes were split. Original: {len(initial_scenes)}, New: {len(final_scenes)}.")

    temp_dir = Path(tempfile.mkdtemp(prefix="txt2video_"))
    
    try:
        print(f"Created temporary directory: {temp_dir}")
        
        scene_data = []
        for i, scene_text in enumerate(final_scenes, 1):
            print(f"Processing Scene {i}/{len(final_scenes)} (Audio)...")
            audio_path, audio_duration = generate_audio(scene_text, temp_dir, i, args.voice)
            print(f"  - Audio: {audio_path.name} ({audio_duration:.2f}s)")
            scene_data.append({"scene_num": i, "text": scene_text, "audio_path": audio_path, "duration": audio_duration})

        video_segments = []
        video_w, video_h = map(int, args.resolution.split('x'))
        margin = 100
        max_text_width = video_w - (2 * margin)

        for data in scene_data:
            scene_num = data['scene_num']
            scene_text = data['text']
            print(f"Processing Scene {scene_num}/{len(final_scenes)} (Video)...")
            wrapped_text = wrap_text(scene_text, font_file, args.font_size, max_text_width)
            video_path = generate_video_segment(data, args, temp_dir, wrapped_text, font_file)
            print(f"  - Video: {video_path.name}")
            video_segments.append(video_path)

        print("All scene segments generated.")
        
        print("Concatenating video segments...")
        concatenate_videos(video_segments, args.output, temp_dir)
        
        print(f"Video generation complete. Output file: {args.output}")

    except Exception as e:
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print("--- FFmpeg/Say Error Output ---", file=sys.stderr)
            print(e.stderr.decode(), file=sys.stderr)
            print("-----------------------------", file=sys.stderr)
        raise
    finally:
        if temp_dir.exists():
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()