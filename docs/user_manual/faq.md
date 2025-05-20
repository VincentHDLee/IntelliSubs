# Frequently Asked Questions (FAQ)

This section will be populated with common questions and answers as the project develops and users provide feedback. Here are some potential FAQs:

---

**Q1: What are the system requirements for IntelliSubs?**
A1: Please refer to the [Installation Guide](./installation.md#system-requirements) for detailed system requirements. Generally, a modern Windows 10/11 64-bit system is needed, with more RAM and a dedicated NVIDIA GPU recommended for better performance.

---

**Q2: Which audio/video file formats does IntelliSubs support?**
A2: IntelliSubs supports common formats like MP3, WAV, M4A for audio, and MP4, MOV, MKV for video (from which audio is extracted). See the [Input and Output](./features/input_output.md#supported-input-file-types) section for a more comprehensive list.

---

**Q3: How accurate is the Japanese speech recognition?**
A3: Accuracy depends on several factors, including the quality of the input audio, the chosen Whisper model size, and the clarity of the speech. For its target of AI-generated standard Japanese voice, accuracy is generally high. Using larger models (e.g., "medium" or "large") can improve accuracy for more complex audio but will take longer to process. The custom dictionary feature can also help improve accuracy for specific terms.

---

**Q4: Can I use IntelliSubs for languages other than Japanese?**
A4: Version 1.1 of IntelliSubs is specifically optimized and targeted for the Japanese market and Japanese language audio. While the underlying Whisper model is multilingual, the current application UI and post-processing steps are tailored for Japanese. Future versions might consider broader multilingual support.

---

**Q5: Does IntelliSubs require an internet connection?**
A5:
*   **For core ASR processing (offline):** Once the ASR models (e.g., Whisper model files) are downloaded to your computer, an internet connection is **not** required for transcription.
*   **For LLM Enhancement:** If you enable the LLM Enhancement feature using a cloud-based LLM service (like OpenAI's API), an active internet connection **is** required.
*   **For Model Downloads:** An internet connection is needed the first time you use a specific ASR model if it's not bundled and needs to be downloaded.

---

**Q6: Where are my settings and ASR models stored?**
A6:
*   **Settings:** Application settings (like default model, paths, API keys) are typically stored in a `config.json` file located in your user's application data directory (e.g., `%APPDATA%\IntelliSubs` on Windows) or in the application's folder if running in portable mode.
*   **ASR Models:** Downloaded Whisper models are usually stored in a cache directory managed by the `faster-whisper` library, often within your user profile (e.g., `~/.cache/huggingface/hub` or a path specific to `faster-whisper`).

---

**Q7: Why is the processing so slow? / How can I speed it up?**
A7:
*   **Use a GPU:** If you have a compatible NVIDIA GPU, ensure it's selected in the settings. GPU processing is significantly faster than CPU.
*   **Select a Smaller ASR Model:** Larger models (medium, large) are more accurate but slower. Try a smaller model (small, base) if speed is critical and audio is clear.
*   **CPU Performance:** Your CPU speed directly impacts processing time if not using a GPU.
*   **Audio Length:** Longer audio files naturally take longer.
*   **Disable LLM Enhancement:** LLM processing adds extra time. Disable it if you don't need it or if speed is a priority.

---

**Q8: Can I edit the subtitles directly within IntelliSubs?**
A8: The initial versions of IntelliSubs primarily focus on generation and provide a preview. Direct editing capabilities within the application are not a core feature of v1.1. For editing, it's recommended to export the subtitles (e.g., as SRT) and use dedicated subtitle editing software like Aegisub, Subtitle Edit, or even a text editor.

---

**Q9: What does "LLM Enhancement" do and do I need an API key for it?**
A9: LLM Enhancement uses a Large Language Model (like GPT) to refine the transcribed text for better punctuation, grammar, and naturalness. Yes, if you are using a commercial LLM service like OpenAI, you will need to provide your own API key in the application settings. See [LLM Enhancement documentation](./features/llm_enhancement.md) for details.

---

**Q10: How do I use the Custom Dictionary?**
A10: Create a `.csv` or `.txt` file with `original,corrected` phrases, one per line. Then, in IntelliSubs settings, point to this file. It helps correct specific terms ASR might mishear. See the [Custom Dictionary documentation](./features/custom_dictionary.md) for format details.

---

*(More questions and answers will be added as they arise.)*