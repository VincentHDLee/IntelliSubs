# Feature: ASR (Automatic Speech Recognition) Settings

智字幕 (IntelliSubs) uses OpenAI's Whisper model (via `faster-whisper` for efficiency) as its primary engine for Automatic Speech Recognition. You can configure several ASR-related settings to balance speed, accuracy, and resource usage.

These settings are typically found in the application's **Settings** or **Preferences** panel/dialog.

## 1. Whisper Model Size

Whisper offers several model sizes. Larger models generally provide better accuracy, especially for noisy audio or complex vocabulary, but they require more processing power (CPU/GPU) and memory, and are slower.

Available models (from smallest/fastest to largest/most accurate):

*   **`tiny`** (e.g., `tiny.ja` if a language-specific version is used, or the multilingual `tiny`)
*   **`base`**
*   **`small`** (Often a good balance for decent quality and speed, **recommended default for Japanese AI voice**)
*   **`medium`** (Can provide significant accuracy improvements over `small`)
*   **`large`** (or `large-v1`, `large-v2`, `large-v3`): Highest accuracy, but also the most resource-intensive and slowest.

**How to Choose:**

*   **For clean, standard AI-generated Japanese voice (like Vtubers, voice synthesis):** `small` or even `base` might be sufficient and fast.
*   **For general Japanese content with clear speech:** `small` or `medium` are good choices.
*   **For challenging audio (background noise, multiple speakers, varied accents - though less relevant for the primary target of AI voice):** `medium` or `large` might be necessary, but expect longer processing times.
*   **If speed is paramount and audio quality is high:** `tiny` or `base` can be tried.

The application will default to a recommended model (e.g., `small`). You can change this in the settings. Note that changing models might require the new model file to be downloaded if it hasn't been used before.

## 2. Processing Device (CPU / GPU)

IntelliSubs allows you to choose the device for ASR processing:

*   **CPU:**
    *   Uses your computer's main processor.
    *   Available on all systems.
    *   Processing will be significantly slower compared to using a dedicated GPU, especially for larger models.
*   **GPU (CUDA for NVIDIA GPUs):**
    *   Uses your NVIDIA graphics card for computation.
    *   **Highly recommended for much faster processing speeds.**
    *   Requires a compatible NVIDIA GPU and correctly installed CUDA drivers.
    *   If a compatible GPU is not detected or drivers are missing, this option might be disabled or the application will automatically fall back to CPU.

**Automatic Detection vs. Manual Selection:**

*   The application may attempt to **auto-detect** a compatible GPU on startup and select it by default.
*   You can typically **manually switch** between CPU and GPU in the settings. If you select GPU but it's not available/working, the application should ideally fall back to CPU and notify you.

## 3. Compute Type (Advanced - for `faster-whisper`)

`faster-whisper` allows specifying the compute type, which affects precision and speed, particularly on GPUs. Common options include:

*   **`float32`:** Standard single-precision floating point. Good balance, default for CPU.
*   **`float16`:** Half-precision. Faster on compatible GPUs, uses less VRAM, with minimal accuracy loss for many models. Often a good choice for GPUs.
*   **`int8_float16`:** Quantized to 8-bit integers with float16 computation. Even faster and less VRAM, potential for slight accuracy drop.
*   **`int8`:** Fully 8-bit quantized. Fastest, lowest VRAM, but may have a more noticeable accuracy impact.

**Recommendation:**

*   **For CPU:** `float32` is typically used.
*   **For GPU (NVIDIA):** `float16` is often a good starting point for a balance of speed and accuracy. If you have a very powerful GPU or are VRAM-constrained with large models, you might experiment with `int8_float16`.
*   The application might choose a sensible default based on the selected device or provide this as an advanced setting.

## 4. Language (Default: Japanese)

While IntelliSubs is optimized for Japanese, Whisper is a multilingual model.
*   The primary language setting will be fixed or defaulted to **Japanese (`ja`)** for this version of IntelliSubs.
*   Future versions or advanced settings *might* allow changing this if other languages become a target, but for v1.1, expect it to be hardcoded or strongly defaulted to Japanese. `faster-whisper`'s `transcribe` method has a `language` parameter.

---

By understanding and adjusting these ASR settings, you can tailor IntelliSubs's performance and accuracy to your specific needs and hardware capabilities. Always ensure your system meets the requirements, especially if opting for GPU processing or larger models.