### **Final Goal Specification for `txt2video`**

**1. Core Objective**
The script's purpose is to convert a text or Markdown file into a narrated video.

**2. Scene Segmentation**
*   The input text is divided into scenes.
    *   For plain text (`.txt`), scenes are separated by one or more blank lines.
    *   For Markdown (`.md`), scenes are separated by a thematic break (`---`).
*   **Automatic Splitting**: If a plain text scene is too long to fit on a single screen, it is automatically split into multiple, screen-sized sub-scenes. (This does not apply to Markdown scenes).

**3. Video Generation**
Each scene becomes a video segment with the following properties:
*   **Narration**: The text of the scene is read aloud using the system's text-to-speech (TTS) engine. For Markdown, all formatting is stripped before narration.
*   **Visuals**: The text is displayed on screen as subtitles over a configurable background.
*   **Timing**: The duration of each video segment is determined by the length of its narration.

**4. Text Layout**
The on-screen text must be correctly formatted:
*   It must be **left-aligned**.
*   It must have **margins** on all sides.
*   It must **wrap automatically**. The wrapping is character-based to correctly handle both space-separated and non-space-separated languages (like Chinese).

**5. Command-Line Interface**
The script must be configurable via the following command-line options, each with a sensible default:
*   `--output <file>`: Specify the output video file name.
*   `--resolution <WxH>`: Set the video resolution.
*   `--bg-color <color>`: Set the video background color.
*   `--bg-image <path>`: Use an image for the background (overrides `--bg-color`).
*   `--voice <name>`: Set the TTS voice.
*   `--font-file <path>`: Path to a `.ttf` or `.ttc` font file.
*   `--font-size <num>`: Set the font size.
*   `--help`: Display a help message.

**6. Robustness**
*   The script is compatible with standard macOS environments and handles errors gracefully.
*   **CJK Support**: The script automatically detects Chinese characters and switches to a suitable system font (`PingFang.ttc`) and TTS voice (`Tingting`) to ensure correct rendering and narration.
*   **Markdown Support**: The script can process Markdown files by converting them to plain text for rendering. It does not render rich formatting like bold or italics.
