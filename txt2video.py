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

def segment_text(file_path, max_chars):
    """
    Reads a text file and splits it into scenes based on blank lines.
    """
    try:
        text = Path(file_path).read_text()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{file_path}'", file=sys.stderr)
        sys.exit(1)
    scenes = re.split(r'\n\s*\n', text.strip())
    validated_scenes = []
    for i, scene in enumerate(scenes, 1):
        scene_text = scene.strip()
        if not scene_text:
            continue
        if len(scene_text) > max_chars:
            print(f"Warning: Scene {i} exceeds --max-chars limit of {max_chars}. Truncating.", file=sys.stderr)
            validated_scenes.append(scene_text[:max_chars])
        else:
            validated_scenes.append(scene_text)
    if not validated_scenes:
        print("Error: No valid scenes found in input file.", file=sys.stderr)
        sys.exit(1)
    return validated_scenes

def generate_audio(scene_text, temp_dir, scene_num, voice=None):
    """
    Generates a narrated audio file for a scene.
    """
    audio_file_aiff = temp_dir / f"scene_{scene_num}.aiff"
    audio_file_m4a = temp_dir / f"scene_{scene_num}.m4a"
    text_file = temp_dir / f"scene_{scene_num}_text.txt"
    text_file.write_text(scene_text, encoding='utf-8')

    cmd_say = ["say", "-o", str(audio_file_aiff), "-f", str(text_file)]
    if voice:
        cmd_say.extend(["-v", voice])
    subprocess.run(cmd_say, check=True, capture_output=True)

    cmd_ffmpeg = ["ffmpeg", "-y", "-i", str(audio_file_aiff), "-c:a", "aac", "-b:a", "192k", str(audio_file_m4a)]
    subprocess.run(cmd_ffmpeg, check=True, capture_output=True)

    cmd_ffprobe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file_m4a)]
    result = subprocess.run(cmd_ffprobe, check=True, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    return audio_file_m4a, duration

def wrap_text(text, font_file, font_size, max_width, max_height):
    """
    Wraps text to fit within a specified width.
    Checks if the wrapped text exceeds a maximum height.
    Returns the wrapped text and a boolean indicating if it overflowed.
    """
    try:
        font = ImageFont.truetype(font_file, font_size) if font_file else ImageFont.load_default()
    except IOError:
        print(f"Warning: Could not load font file '{font_file}'. Using Pillow's default.", file=sys.stderr)
        font = ImageFont.load_default()

    # 1. Horizontal Wrapping
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

    # 2. Check for Vertical Overflow
    line_height = sum(font.getmetrics())
    total_height = len(lines) * line_height
    overflows = total_height > max_height
    
    return "\n".join(lines), overflows

def generate_video_segment(scene_data, args, temp_dir, wrapped_text, font_file):
    """
    Generates a video segment for a single scene.
    """
    scene_num = scene_data["scene_num"]
    duration = scene_data["duration"]
    audio_path = scene_data["audio_path"]
    video_path = temp_dir / f"scene_{scene_num}.mp4"

    margin = 100
    # Escape text for ffmpeg filter
    escaped_text = wrapped_text.replace("\\", "\\").replace("'", "’").replace(":", "\:").replace("%", "\%")
    
    font_arg = ""
    if font_file:
        # Prepare font file path for ffmpeg, handling Windows paths
        resolved_path = Path(font_file).resolve()
        ffmpeg_font_path = str(resolved_path).replace("\\", "/")
        ffmpeg_font_path = ffmpeg_font_path.replace(":", "\:")
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
    
    # Prepend the main ffmpeg executable
    final_cmd = ["ffmpeg", "-y"] + cmd_ffmpeg
    subprocess.run(final_cmd, check=True, capture_output=True)
    return video_path


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
    parser.add_argument("--max-chars", type=int, default=280, help="Set the maximum characters allowed per scene.\n(default: 280)")

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

    scenes = segment_text(args.input_file, args.max_chars)
    temp_dir = Path(tempfile.mkdtemp(prefix="txt2video_"))
    
    try:
        print(f"Created temporary directory: {temp_dir}")
        
        # 1. Generate audio and gather data
        scene_data = []
        for i, scene_text in enumerate(scenes, 1):
            print(f"Processing Scene {i}/{len(scenes)} (Audio)...")
            audio_path, audio_duration = generate_audio(scene_text, temp_dir, i, args.voice)
            print(f"  - Audio: {audio_path.name} ({audio_duration:.2f}s)")
            scene_data.append({"scene_num": i, "text": scene_text, "audio_path": audio_path, "duration": audio_duration})

        # 2. Generate video segments
        video_segments = []
        video_w, video_h = map(int, args.resolution.split('x'))
        margin = 100
        max_text_width = video_w - (2 * margin)
        max_text_height = video_h - (2 * margin)

        # --- Font setup ---
        font_file = args.font_file
        if font_file and Path(font_file).exists():
            print(f"Using user-provided font: {font_file}")
        else:
            if font_file: # Provided but not found
                print(f"Warning: Font file '{font_file}' not found.", file=sys.stderr)
            
            default_font_path = ""
            if sys.platform == "darwin":
                default_font_path = "/System/Library/Fonts/Helvetica.ttc"
            elif sys.platform == "linux":
                # Common location for a standard font
                default_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

            if default_font_path and Path(default_font_path).exists():
                font_file = default_font_path
                print(f"Using default system font: {font_file}")
            else:
                font_file = None
                print("Warning: Could not find a default system font.", file=sys.stderr)
                print("Text wrapping may be inaccurate as a fallback font will be used.", file=sys.stderr)

        for data in scene_data:
            scene_num = data['scene_num']
            scene_text = data['text']
            
            print(f"Processing Scene {scene_num}/{len(scenes)} (Video)...")
            wrapped_text, overflows = wrap_text(
                scene_text, font_file, args.font_size, max_text_width, max_text_height
            )
            
            if overflows:
                print(f"\n--- ERROR: Scene {scene_num} is too long to fit on the screen. ---", file=sys.stderr)
                print("Please split this scene into smaller parts in your input file.", file=sys.stderr)
                print("\nProblematic scene content:", file=sys.stderr)
                print(f"'{scene_text}'", file=sys.stderr)
                sys.exit(1)

            video_path = generate_video_segment(data, args, temp_dir, wrapped_text, font_file)
            print(f"  - Video: {video_path.name}")
            video_segments.append(video_path)

        print("All scene segments generated.")
        
        # 3. Concatenate video segments
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

def concatenate_videos(video_paths, output_file, temp_dir):
    """
    Concatenates multiple video files into a single file using ffmpeg.
    """
    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w") as f:
        for path in video_paths:
            # Path needs to be escaped for ffmpeg's concat demuxer
            escaped_path = str(path).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(Path(output_file).resolve())
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("Error during video concatenation:", file=sys.stderr)
        print("FFmpeg command:", " ".join(cmd))
        print(e.stderr.decode(), file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
