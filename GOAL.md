### **Final Goal Specification for `txt2video`**

**1. Core Objective**
The script's purpose is to convert a text or Markdown file into a narrated video.

**2. Scene Segmentation**
*   The input text is divided into scenes based on blank lines.
*   For Markdown files, the content is first converted to plain text, preserving paragraph structure, and then split by blank lines.
*   **Automatic Splitting**: If a scene is too long to fit on a single screen, it is automatically split into multiple, screen-sized sub-scenes.

**3. Video Generation**
Each scene becomes a video segment with the following properties:
*   **Narration**: The text of the scene is read aloud using the system's text-to-speech (TTS) engine.
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
*   **CJK Support**: The script automatically detects Chinese characters and switches to a suitable system font and TTS voice to ensure correct rendering and narration. Users can override this by providing their own font if the default one lacks specific characters.