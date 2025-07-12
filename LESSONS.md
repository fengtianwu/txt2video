### **Summary of Problems and Lessons Learned**

1.  **Problem: Shell Scripting Fragility**
    *   **Issue**: The shell script was plagued by repeated, subtle syntax errors (`unexpected EOF`, unclosed quotes, etc.), especially when parsing text and handling variables. The `while read` loops were particularly fragile.
    *   **Lesson**: For tasks involving complex string manipulation, process orchestration (calling `ffmpeg`, `ffprobe`), and floating-point math, shell scripting is the wrong tool. It is not robust enough. **Python is the correct tool for this job.**

2.  **Problem: Floating-Point Math in Shell**
    *   **Issue**: The script failed with an `invalid arithmetic operator` error because the standard shell syntax `$((...))` does not support floating-point numbers (e.g., `5.73`).
    *   **Lesson**: All floating-point calculations must be handled by a tool that explicitly supports them, like `bc` or, more appropriately, Python's native math capabilities.

3.  **Problem: Text Wrapping in `ffmpeg`**
    *   **Issue**: The `drawtext` filter in `ffmpeg` does not handle automatic text wrapping reliably for multi-line blocks. My attempts to fix this with subtitle styling tags (`\\q`, `\\clip`) were also incorrect, as they did not address the root cause: the renderer calculates wrapping based on the full video width, not the margin-adjusted width.
    *   **Lesson**: Do not rely on the `ffmpeg` filters to perform "smart" text wrapping. The most reliable solution is to **manually pre-wrap the text** to the correct width *before* passing it to `ffmpeg`. This removes all ambiguity.

4.  **Problem: Monolithic Development**
    *   **Issue**: By attempting to write the entire script in one step, any single error caused the whole process to fail, making debugging extremely difficult and leading to a cascade of patches.
    *   **Lesson**: A **modular, step-by-step development process** is required. Each component (e.g., text parsing, audio generation, video segment creation) must be built and verified independently before being integrated.

