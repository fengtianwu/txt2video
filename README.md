# txt2video

A Python script to convert a text or Markdown file into a narrated video using system tools.

This tool takes a simple text or Markdown file, splits it into scenes, generates narration using the system's Text-to-Speech (TTS) engine, and combines it all into a video file with the text displayed on screen.

## Features

- **Multi-Format Support**: Handles both plain text (`.txt`) and Markdown (`.md`) files.
- **Scene Segmentation**:
    - For `.txt` files, splits scenes by blank lines.
    - For `.md` files, splits scenes by thematic breaks (`---`).
- **Automatic Scene Splitting**: If a plain text scene is too long to fit on a single screen, it's automatically divided into multiple, perfectly sized sub-scenes.
- **Text-to-Speech Narration**: Each scene is narrated using the system's TTS engine.
- **Intelligent Font Handling**:
    - Automatically detects and wraps text for both English and CJK (Chinese, Japanese, Korean) languages.
    - On macOS, automatically selects a system font that supports Chinese characters if detected.
- **Customizable Visuals**: Configure video resolution, background color, or use a background image and custom fonts.

## Requirements

- Python 3.x
- **Pillow** (`pip install Pillow`)
- **Markdown** (`pip install markdown`)
- **BeautifulSoup4** (`pip install beautifulsoup4`)
- **ffmpeg** and `ffprobe` (must be in your system's PATH)
- **macOS only**: The `say` command-line tool (pre-installed).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/txt2video.git
    cd txt2video
    ```

2.  Install the required Python libraries:
    ```bash
    pip install Pillow markdown beautifulsoup4
    ```

3.  Ensure `ffmpeg` is installed. If you use Homebrew on macOS:
    ```bash
    brew install ffmpeg
    ```

## Usage

The script is run from the command line.

```bash
./txt2video.py [input_file] [options]
```

### Options

| Argument | Default | Description |
|---|---|---|
| `input_file` | (required) | Path to the input text or Markdown file. |
| `--output` | `output.mp4` | Name of the output video file. |
| `--resolution` | `1920x1080` | Video resolution (e.g., `1280x720`). |
| `--bg-color` | `black` | Background color. |
| `--bg-image` | `None` | Path to a background image (overrides bg-color). |
| `--voice` | `None` | Name of the TTS voice to use (e.g., "Alex"). |
| `--font-file`| `None` | Path to a custom `.ttf` or `.ttc` font file. |
| `--font-size`| `36` | Font size for the on-screen text. |
| `--help` | | Displays the help message. |

### Examples

**Basic Conversion**
```bash
./txt2video.py my_script.txt
```

**Processing a Markdown File**

Create a file `story.md`:
```markdown
# Chapter 1

This is the first scene. It has **bold** text.

---

This is the second scene. The script will strip the formatting and read the plain text.
```

The script will convert the Markdown to plain text for narration and rendering.

```bash
./txt2video.py story.md
```

## License

This project is licensed under the MIT License.