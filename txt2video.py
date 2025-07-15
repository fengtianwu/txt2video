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
try:
    import markdown
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 'markdown' and 'beautifulsoup4' are required. Please install them with: pip install markdown beautifulsoup4", file=sys.stderr)
    sys.exit(1)

# --- Font Path Configuration ---
#FONT_PATH_FOR_CJK = "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/PingFang.ttc"
FONT_PATH_FOR_CJK = "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/9d5450ee93f17da1eacfa01b5e7b598f9e2dda2b.asset/AssetData/Baoli.ttc"

FONT_PATH_DEFAULT = "/System/Library/Fonts/Helvetica.ttc"


def check_command_exists(command):
    """Check if a command exists on the system."""
    if not shutil.which(command):
        print(f"Error: '{command}' is not installed or not in your PATH.", file=sys.stderr)
        sys.exit(1)

def segment_text(file_path):
    """
    Reads a text or markdown file and splits it into scenes based on blank lines.
    If the file is markdown, it's converted to plain text while preserving paragraph breaks.
    """
    try:
        raw_text = Path(file_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"Error: Input file not found at '{file_path}'", file=sys.stderr)
        sys.exit(1)

    # If it's a markdown file, convert to plain text first.
    if Path(file_path).suffix.lower() in ['.md', '.markdown']:
        print("Markdown file detected. Converting to plain text for processing.")
        # Use the 'extra' extension for better handling of things like fenced code
        html = markdown.markdown(raw_text, extensions=['extra'])
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all block-level elements and join their text with double newlines
        # to preserve the scene breaks that the splitter relies on.
        blocks = [tag.get_text(" ", strip=True) for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'pre', 'blockquote'])]
        text = "\n\n".join(blocks)
    else:
        text = raw_text
        
    # Now, split the resulting text by one or more blank lines
    scenes = re.split(r'\n\s*\n', text.strip())
    
    validated_scenes = [scene.strip() for scene in scenes if scene.strip()]
    if not validated_scenes:
        print("Error: No valid scenes found in input file.", file=sys.stderr)
        sys.exit(1)
    return validated_scenes

def generate_audio(scene_text, temp_dir, scene_num, voice=None):
    """
    Generates a narrated audio file for a scene using macOS 'say' command.
    """
    audio_file_aiff = temp_dir / f"scene_{scene_num}.aiff"
    audio_file_m4a = temp_dir / f"scene_{scene_num}.m4a"
    text_file = temp_dir / f"scene_{scene_num}_text.txt"
    text_file.write_text(scene_text, encoding='utf-8')

    voice_to_use = voice
    if not voice_to_use and any("\u4e00" <= char <= "\u9fff" for char in scene_text):
        voice_to_use = "Tingting"

    cmd_say = ["say", "-o", str(audio_file_aiff), "-f", str(text_file)]
    if voice_to_use:
        cmd_say.extend(["-v", voice_to_use])
    
    try:
        subprocess.run(cmd_say, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio for scene {scene_num} with 'say':", file=sys.stderr)
        print(e.stderr.decode(), file=sys.stderr)
        if "voice not found" in e.stderr.decode().lower():
            print(f"\nHint: The voice '{voice_to_use}' was not found on your system.", file=sys.stderr)
            print("You can list available voices with: say -v '?'", file=sys.stderr)
        raise

    audio_file_aiff_raw = temp_dir / f"scene_{scene_num}_raw.aiff" # Raw output from say
    audio_file_aiff_silent = temp_dir / f"scene_{scene_num}_silent.aiff" # After adding silence
    audio_file_m4a = temp_dir / f"scene_{scene_num}.m4a"
    text_file = temp_dir / f"scene_{scene_num}_text.txt"
    text_file.write_text(scene_text, encoding='utf-8')

    voice_to_use = voice
    if not voice_to_use and any("\u4e00" <= char <= "\u9fff" for char in scene_text):
        voice_to_use = "Tingting"

    cmd_say = ["say", "-o", str(audio_file_aiff_raw), "-f", str(text_file)]
    if voice_to_use:
        cmd_say.extend(["-v", voice_to_use])

    try:
        subprocess.run(cmd_say, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio for scene {scene_num} with 'say':", file=sys.stderr)
        print(e.stderr.decode(), file=sys.stderr)
        if "voice not found" in e.stderr.decode().lower():
            print(f"\nHint: The voice '{voice_to_use}' was not found on your system.", file=sys.stderr)
            print("You can list available voices with: say -v '?'", file=sys.stderr)
        raise

    # Add 0.5 seconds of silence to the beginning of the audio
    silence_duration = 0.5
    sample_rate = 44100 # Default sample rate for 'say' command output
    cmd_add_silence = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=duration={silence_duration}:sample_rate={sample_rate}",
        "-i", str(audio_file_aiff_raw),
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
        "-map", "[out]",
        str(audio_file_aiff_silent)
    ]
    subprocess.run(cmd_add_silence, check=True, capture_output=True)

    # Convert the silent AIFF to M4A
    cmd_ffmpeg_convert = ["ffmpeg", "-y", "-i", str(audio_file_aiff_silent), "-c:a", "aac", "-b:a", "192k", str(audio_file_m4a)]
    subprocess.run(cmd_ffmpeg_convert, check=True, capture_output=True)

    # Get the duration of the final M4A file (which now includes silence)
    cmd_ffprobe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file_m4a)]
    result = subprocess.run(cmd_ffprobe, check=True, capture_output=True, text=True)
    duration = float(result.stdout.strip())

    return audio_file_m4a, duration

def wrap_text(text, font, max_width):
    """
    Wraps text to fit within a specified width using character-by-character measurement.
    """
    lines = []
    current_line = ""
    for char in text:
        if char == '\n':
            lines.append(current_line)
            current_line = ""
            continue
        
        test_line = f"{current_line}{char}"
        if font.getbbox(test_line)[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    
    return "\n".join(lines)

def generate_video_segment(scene_data, args, temp_dir, wrapped_text, font_path):
    """
    Generates a video segment for a single scene.
    """
    scene_num = scene_data["scene_num"]
    duration = scene_data["duration"]
    audio_path = scene_data["audio_path"]
    video_path = temp_dir / f"scene_{scene_num}.mp4"

    margin = 100
    escaped_text = wrapped_text.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%")
    
    font_file_for_ffmpeg = font_path.replace(":", "\\:")
    
    drawtext_filter = (
        f"drawtext=fontfile='{font_file_for_ffmpeg}':text='{escaped_text}':"
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

def resplit_long_scenes(scenes, font, max_width, max_height):
    """
    Takes a list of scenes and splits any that are too long into smaller sub-scenes.
    """
    line_height = sum(font.getmetrics())
    if line_height == 0:
        return scenes
    max_lines_per_scene = max_height // line_height

    final_scenes = []
    for scene_text in scenes:
        lines = wrap_text(scene_text.replace('\n', ' '), font, max_width).split('\n')

        if len(lines) <= max_lines_per_scene:
            final_scenes.append(scene_text)
        else:
            for i in range(0, len(lines), max_lines_per_scene):
                chunk = lines[i:i + max_lines_per_scene]
                final_scenes.append("\n".join(chunk))
                
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

    args = parser.parse_args()
    if not args.input_file:
        parser.print_help(sys.stderr)
        sys.exit(1)

    check_command_exists("say")
    check_command_exists("ffmpeg")
    check_command_exists("ffprobe")

    initial_scenes = segment_text(args.input_file)
    contains_chinese = any("\u4e00" <= char <= "\u9fff" for scene in initial_scenes for char in scene)
    
    font_path = args.font_file
    if not font_path:
        font_path = FONT_PATH_FOR_CJK if contains_chinese else FONT_PATH_DEFAULT
    
    print(f"Using font: {font_path}")
    
    try:
        font = ImageFont.truetype(font_path, args.font_size)
    except IOError:
        print(f"Fatal: Could not load font '{font_path}'. Please check the path or provide a valid one with --font-file.", file=sys.stderr)
        sys.exit(1)

    video_w, video_h = map(int, args.resolution.split('x'))
    margin = 100
    max_text_width = video_w - (2 * margin)
    max_text_height = video_h - (2 * margin)

    final_scenes = resplit_long_scenes(initial_scenes, font, max_text_width, max_text_height)
    if len(final_scenes) > len(initial_scenes):
        print(f"Long scenes were split. Original: {len(initial_scenes)}, New: {len(final_scenes)}.")

    temp_dir = Path(tempfile.mkdtemp(prefix="txt2video_"))
    
    try:
        print(f"Created temporary directory: {temp_dir}")
        
        scene_data = []
        for i, scene_text in enumerate(final_scenes, 1):
            print(f"Processing Scene {i}/{len(final_scenes)} (Audio)...")
            audio_path, audio_duration = generate_audio(scene_text, temp_dir, i, args.voice)
            scene_data.append({"scene_num": i, "text": scene_text, "audio_path": audio_path, "duration": audio_duration})

        video_segments = []
        for data in scene_data:
            scene_num = data['scene_num']
            scene_text = data['text']
            print(f"Processing Scene {scene_num}/{len(final_scenes)} (Video)...")
            wrapped_text = wrap_text(scene_text, font, max_text_width)
            video_path = generate_video_segment(data, args, temp_dir, wrapped_text, font_path)
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
