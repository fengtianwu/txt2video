# txt2video

A Python script to convert a plain text file into a narrated video using system tools.

This tool takes a simple text file, splits it into scenes, generates narration using the system's Text-to-Speech (TTS) engine, and combines it all into a video file with the text displayed on screen.

## Features

- **Scene Segmentation**: Automatically splits text into scenes based on blank lines.
- **Automatic Scene Splitting**: If a scene is too long to fit on a single screen, it's automatically divided into multiple, perfectly sized sub-scenes.
- **Text-to-Speech Narration**: Each scene is narrated using the system's TTS engine.
- **Customizable Visuals**: Configure video resolution, background color, or use a background image.
- **Intelligent Font Handling**:
    - Automatically detects and wraps text for both English and CJK (Chinese, Japanese, Korean) languages.
    - On macOS, automatically selects a system font that supports Chinese characters if detected (`PingFang.ttc`).
- **Custom Fonts**: Specify a path to your own `.ttf` or `.ttc` font file.

## Requirements

- Python 3.x
- [Pillow](https://python-pillow.org/) library (`pip install Pillow`)
- [ffmpeg](https://ffmpeg.org/) and `ffprobe` (must be in your system's PATH)
- **macOS only**: The `say` command-line tool (pre-installed).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/txt2video.git
    cd txt2video
    ```

2.  Install the required Python library:
    ```bash
    pip install Pillow
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
| `input_file` | (required) | Path to the input text file. |
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

**Custom Output and Resolution**
```bash
./txt2video.py my_script.txt --output my_video.mp4 --resolution 1280x720
```

**Using a Background Image and a Specific Voice**
```bash
./txt2video.py my_script.txt --bg-image /path/to/background.jpg --voice "Daniel"
```

**Generating a Video with Chinese Text**

Create a file `chinese.txt`:
```
这是第一个场景。

这是一个非常长的中文场景，用来测试自动分屏功能。
```

The script will automatically detect the Chinese characters, select a compatible font and TTS voice ("Tingting") on macOS.

```bash
./txt2video.py chinese.txt
```

To use a different Chinese voice, find one available on your system (`say -v '?'`) and specify it:
```bash
./txt2video.py chinese.txt --voice "Mei-Jia"
```

## License

This project is licensed under the MIT License.
