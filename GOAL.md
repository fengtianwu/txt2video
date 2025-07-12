### **Final Goal Specification for `txt2video`**

**1. Core Objective**
The script's purpose is to convert a plain text file into a narrated video.

**2. Scene Segmentation**
The input text is divided into scenes. Each scene is a block of text separated by one or more blank lines.

**3. Video Generation**
Each scene becomes a video segment with the following properties:
*   **Narration**: The text of the scene is read aloud using a system text-to-speech (TTS) engine.
*   **Visuals**: The text is displayed on screen as subtitles over a configurable background.
*   **Timing**: The duration of each video segment is determined by the length of its narration.

**4. Text Layout**
The on-screen text must be correctly formatted:
*   It must be **left-aligned**.
*   It must have **margins** on all sides.
*   It must **wrap automatically** without words being cut off.

**5. Command-Line Interface**
The script must be configurable via the following command-line options, each with a sensible default:
*   `--output <file>`: Specify the output video file name.
*   `--resolution <WxH>`: Set the video resolution.
*   `--bg-color <color>`: Set the video background color.
*   `--bg-image <path>`: Use an image for the background (overrides `--bg-color`).
*   `--voice <name>`: Set the TTS voice.
*   `--font-file <path>`: Path to a `.ttf` or `.ttc` font file.
*   `--font-size <num>`: Set the font size.
*   `--max-chars <num>`: Set the maximum characters allowed per scene.
*   `--help`: Display a help message.

**6. Development Methodology**
*   **Principle 1: Use the Right Tool**: The implementation will be done in **Python**.
*   **Principle 2: Modular, Incremental Development**: The script will be built and confirmed in small, functional modules before final integration.

**7. Robustness**
The script must be compatible with standard macOS and Linux environments and handle errors gracefully.
