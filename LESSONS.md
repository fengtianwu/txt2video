### **Summary of Problems and Lessons Learned**

1.  **Problem: Shell Scripting Fragility**
    *   **Issue**: The initial shell script was plagued by repeated, subtle syntax errors (`unexpected EOF`, unclosed quotes, etc.), especially when parsing text and handling variables.
    *   **Lesson**: For tasks involving complex string manipulation, process orchestration (calling `ffmpeg`, `ffprobe`), and floating-point math, shell scripting is the wrong tool. It is not robust enough. **Python is the correct tool for this job.**

2.  **Problem: Floating-Point Math in Shell**
    *   **Issue**: The script failed with an `invalid arithmetic operator` error because the standard shell syntax `$((...))` does not support floating-point numbers.
    *   **Lesson**: All floating-point calculations must be handled by a tool that explicitly supports them, like `bc` or, more appropriately, Python's native math capabilities.

3.  **Problem: Text Wrapping in `ffmpeg`**
    *   **Issue**: The `drawtext` filter in `ffmpeg` does not handle automatic text wrapping reliably. The root cause is that the renderer calculates wrapping based on the full video width, not a margin-adjusted width.
    *   **Lesson**: Do not rely on `ffmpeg` filters to perform "smart" text wrapping. The most reliable solution is to **manually pre-wrap the text** to the correct width *before* passing it to `ffmpeg`.

4.  **Problem: Monolithic Development**
    *   **Issue**: By attempting to write the entire script in one step, any single error caused the whole process to fail, making debugging extremely difficult.
    *   **Lesson**: A **modular, step-by-step development process** is required. Each component (e.g., text parsing, audio generation, video segment creation) must be built and verified independently.

5.  **Problem: Font Rendering and Measurement Mismatches**
    *   **Issue**: The script initially failed to render Chinese characters (showing "tofu" squares) and wrapped them incorrectly. This was caused by three distinct issues:
        1.  The font used for measuring text (`Pillow`) was not the same as the font used for rendering (`ffmpeg`), leading to inaccurate line breaks.
        2.  The default system font did not contain glyphs for Chinese characters.
        3.  The text-wrapping logic was word-based (splitting on spaces), which fails for languages like Chinese.
    *   **Lesson**: For robust multilingual text rendering:
        1.  **Unify Font Handling**: Ensure the exact same font file (`.ttf`, `.ttc`) is used for both text measurement and video rendering.
        2.  **Use CJK-Compatible Fonts**: When Chinese, Japanese, or Korean text is detected, the script must automatically select a font known to support those characters (e.g., `PingFang.ttc` on macOS).
        3.  **Wrap Character-by-Character**: Text wrapping logic must not assume words are separated by spaces. Iterating character-by-character is the only reliable way to handle both Western and CJK languages correctly.

6.  **Problem: System Command Integration is Fragile**
    *   **Issue**: Finding the correct path to system fonts is unreliable; hardcoded paths like `/System/Library/Fonts/PingFang.ttc` can be incorrect. Additionally, the macOS `say` command failed silently when a voice was unavailable or misnamed (`Ting-Ting` vs. `Tingting`).
    *   **Lesson**: Do not guess system resource paths. The most reliable method is to use a system utility to find the exact resource location (e.g., `system_profiler SPFontsDataType` on macOS). For system commands, add robust error handling that checks for failures and provides users with helpful diagnostic hints (e.g., "Voice not found, run `say -v '?'` to see available voices.").