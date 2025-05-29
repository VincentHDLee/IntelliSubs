# LLM Enhancement - Feature Improvements and Discussion Points

## Current Status (as of 2025-05-26)
- LLM requests correctly target the `/v1/chat/completions` endpoint.
- The UI allows dynamic fetching of models from `/v1/models` and selection via a dropdown menu.
- **Observed Issue**: The currently configured LLM service (`https://sucoiapi.com` with model `gemini-2.5-flash-preview-04-17`) frequently returns empty or semantically null content for the existing hardcoded system prompts. This results in no visible enhancement in the frontend, as the application correctly falls back to the original text.

## New User Requirements & Discussion

### 1. Customizable System Prompt (DI: 4/5)
- **User Request**: Allow users to input a custom System Prompt (often referred to as a "role card" or "persona") directly in the UI. This would replace or override the currently hardcoded system prompts in `llm_enhancer.py`.
- **Status**: To-Do.
- **Rationale**: Hardcoded prompts may not be optimal for all models or custom LLM services. User-defined prompts offer flexibility and better control over the LLM's behavior.
- **Proposed UI Changes**:
    - Add a multi-line text input field (e.g., `CTkTextbox`) within the "AI & Advanced Settings" tab, specifically under the LLM options.
    - Provide a label indicating its purpose (e.g., "Custom LLM System Prompt (Optional)").
    - Consider whether one global custom prompt is sufficient, or if per-language custom prompts are needed (this would add complexity to the UI).
    - A "Reset to Default" button to clear the custom prompt and revert to the application's default (hardcoded or a new configurable default).
- **Configuration**:
    - The custom system prompt (or prompts, if per-language) should be saved in the `config.json` file.
    - Example config keys: `llm_custom_system_prompt` (global) or `llm_custom_system_prompt_ja`, `llm_custom_system_prompt_en`, etc.
- **Backend Implementation**:
    - `LLMEnhancer` should be modified to accept an optional custom system prompt during initialization or via a setter.
    - If a custom prompt is provided and non-empty, it should be used; otherwise, `LLMEnhancer` should fall back to its language-specific internal default prompt.
    - `WorkflowManager` will need to read this custom prompt from the configuration and pass it to `LLMEnhancer`.
- **Open Questions/Considerations**:
    - **Global vs. Per-Language Prompts**: Per-language offers more fine-tuning but increases UI/config complexity. A global prompt is simpler to start with.
    - **Default Prompt Management**: If a user clears their custom prompt, what is the fallback? The current hardcoded ones, or should these also become configurable defaults?

### 2. Batch Processing of Subtitle Segments for LLM Enhancement (DI: 2/5)
- **User Request**: Instead of making one API call to the LLM for each individual subtitle segment, aggregate all segments from a single source file, format them (e.g., as a table or structured list), and send them to the LLM in a single API request. The LLM would then (ideally) process all segments and return all enhanced segments in a single response.
- **Status**: To-Do. Requires significant investigation.
- **Rationale**: To reduce costs for LLM APIs that charge per API call, rather than purely on token count.
- **Core Challenges & Feasibility**:
    - **LLM API Support**: This heavily depends on whether the target LLM API (e.g., `https://sucoiapi.com` or standard OpenAI) supports such batch processing within a single `chat/completions` call. Standard chat models are designed for conversational turns, not typically for batch record processing with structured I/O for each record in one go.
        - Some advanced models support "function calling" or "tool use," which *might* be adaptable for this, but it's complex.
    - **Prompt Engineering**: Crafting a system and user prompt that instructs the LLM to:
        1.  Accept a list/batch of N raw text segments.
        2.  Apply a specific enhancement instruction (e.g., "optimize for clarity and natural language for subtitles") to *each* segment *independently*.
        3.  Return a list of N enhanced text segments, maintaining the original order and ensuring no segments are dropped or merged.
        This is a non-trivial prompting task and highly prone to LLM "misinterpretations."
    - **Input Formatting**: How to best format N segments into a single text block for the LLM (e.g., JSON array as a string, numbered list, CSV-like block).
    - **Output Parsing**: Reliably parsing the LLM's single, large text response back into N individual enhanced segments. If the LLM doesn't adhere strictly to the requested output format (e.g., a JSON array string), parsing will be fragile.
    - **Token Limits**: The combined text of all segments, plus the complex prompt, could easily exceed the LLM's maximum context window/token limit for a single request. This is a major constraint.
    - **Error Propagation**: If one segment in the batch causes an issue for the LLM, it might refuse to process the entire batch, or the quality of all other segments might degrade. Individual calls isolate errors.
    - **Cost vs. Complexity**: While per-call costs might be saved, a single large batch request will consume more tokens. The overall cost benefit needs careful analysis against the significant implementation complexity and potential unreliability.
- **Alternative Approach (if full batching is infeasible)**:
    - Continue with per-segment API calls but optimize further:
        - Ensure efficient use of `asyncio.gather` for maximum concurrency (already in place).
        - Potentially introduce a configurable delay between batches of concurrent requests if rate limiting is an issue with many small, fast calls.
- **Investigation Needed**: Thoroughly review the documentation for `https://sucoiapi.com` to see if any form of batch request or structured input/output for multiple items is officially supported.

## Other Identified Issues & Considerations for LLM Enhancement

### 1. Default Prompt Effectiveness
- **Update (2025-05-29):** The default system and user prompt templates are no longer hardcoded in `llm_enhancer.py`. They are now part of the `DEFAULT_CONFIG` in `ConfigManager` and are written to `config.json` in the project root upon first run (or if the `llm_prompts` key is missing). `LLMEnhancer` loads these from the configuration.
- The prompts in `config.json` (under the `llm_prompts` key) are initial, generic versions designed to request only the subtitle text.
- As observed, their effectiveness can vary significantly between LLM models (e.g., some models might still return empty or suboptimal responses).
- **Recommendation**: Users should be encouraged to customize the `llm_system_prompt` via the UI settings (which overrides any default system prompt) or directly edit the default templates in `config.json` to better suit their chosen LLM model and specific enhancement needs. Testing prompts against a known-good service or the target LLM directly remains a good practice.

### 2. Robustness of LLM API Error Handling
- The current error handling in `LLMEnhancer` catches `httpx.HTTPStatusError` and logs the response.
- **Suggestion**: Enhance this to provide more specific user feedback in the UI for common, actionable errors:
    - **401 Unauthorized**: "LLM API Key is invalid or missing. Please check your settings."
    - **403 Forbidden**: Similar to 401, or could mean quota issues.
    - **429 Too Many Requests**: "LLM rate limit hit. Please try again later or reduce request frequency." (Could implement an automatic backoff/retry for this).
    - **400 Bad Request**: Often indicates an issue with the request payload (e.g., model not supported by endpoint, malformed JSON (unlikely with `httpx`), or incompatible parameters). "LLM request was invalid. Check model name and parameters."
    - **5xx Server Errors**: "LLM service encountered an internal error. Please try again later."

### 3. Per-Language Fallback/Defaults for Custom Prompts
- If custom system prompts are per-language, what happens if a user sets a custom prompt for Japanese but then processes an English file without an English custom prompt set?
- **Solution**: The system should gracefully fall back: Custom Lang Prompt -> Global Custom Prompt (if exists) -> Hardcoded/Default Lang Prompt.

### 4. Model/Endpoint Incompatibility for LLM Requests
- **Issue**: The application currently exclusively uses the `/v1/chat/completions` API endpoint for all LLM interactions. However, some LLM models (e.g., `babbage-002` as observed with `https://sucoiapi.com`) are not chat models and are incompatible with this endpoint.
- **Observed Behavior**: When a non-chat model is selected and LLM enhancement is attempted, the API returns an HTTP 404 error. The error message from the service typically indicates this incompatibility, for example: `{'error': {'message': 'This is not a chat model and thus not supported in the v1/chat/completions endpoint. Did you mean to use v1/completions?', ...}}`.
- **Impact**: This prevents any LLM-based features from working correctly if an incompatible model is selected by the user. The application currently fetches a wide range of models, some ofwhich may be non-chat models.
- **Potential Solutions (for future consideration)**:
    - **Dynamic Endpoint Selection**: Implement logic to choose between `/v1/chat/completions` and `/v1/completions` (or other relevant endpoints) based on model characteristics. This would require a way to identify model type (e.g., from API metadata if available, or heuristics based on model name).
    - **Model Filtering/Tagging in UI**: Improve the model selection UI to either filter out models known to be incompatible with the chat endpoint, or tag models by type to guide user selection.
    - **User-Selectable Endpoint**: Potentially allow advanced users to specify the endpoint, though this adds complexity.
- **Current Status**: Development and testing of LLM-dependent features (e.g., "Import Script for LLM Context", "Customizable System Prompt") are currently blocked/suspended pending resolution of this core interaction issue. The uncommitted code for "Import Script" feature exists locally.

## Proposed Next Steps
1.  **Address Model/Endpoint Incompatibility**: This is currently the primary blocker for LLM features. Decide on a strategy (dynamic endpoint, UI filtering/guidance, etc.) and implement it.
2.  **Discuss & Prioritize other LLM features**: Once the core interaction is stable, review points like "Customizable System Prompt", "Batch Processing", "Import Script" (and commit its existing code).
3.  **Refine Default Prompts**: Regardless of custom prompts, try to improve the internal default prompts.
4.  **Enhance Error Reporting**: Improve UI feedback for specific HTTP errors from the LLM API.

This document will serve as a basis for these improvements.

### 3. Current Prompt and Response Parsing Strategy (Implemented as of 2025-05-29)
- **Objective**: To ensure the LLM returns only the enhanced subtitle text and to robustly extract this text even if the LLM includes extra verbiage.
- **Prompt Design (`LLMEnhancer` default prompts):**
    - System prompts for Japanese, Chinese, and English have been updated to explicitly instruct the LLM:
        - "応答には最適化された字幕テキスト「のみ」を含めてください。説明、マークダウン、書式設定、または「最適化された字幕:」のようなラベルは一切含めないでください。" (JA example)
        - "返回结果时，请「仅」包含优化后的字幕文本。不要添加任何解释、markdown、格式化内容或类似“优化字幕:”的标签。" (ZH example)
        - "In your response, include *only* the optimized subtitle text. Do not add any explanations, markdown, formatting, or labels like 'Optimized Subtitle:'." (EN example)
    - These instructions aim to minimize extraneous output from the LLM.
- **Response Parsing (`LLMEnhancer._parse_llm_response_content` method):**
    - This method is called after receiving the raw text content from the LLM.
    - **Keyword-based Heuristic (First Pass):**
        - It first checks for known headers/keywords (e.g., "最適化された字幕:", "**Adjustment Points:**", "优化字幕:", etc.).
        - If such a keyword is found, it attempts to extract the text immediately following it, and then tries to strip any subsequent explanation blocks from this extracted portion.
        - Markdown (`**`) is removed from this heuristically extracted text.
        - If this process yields a non-empty string, it's returned as the cleaned subtitle.
    - **Line-by-Line Processing (Second Pass, if keyword heuristic fails or yields nothing):**
        - Splits the raw content into lines.
        - Iterates through lines, skipping empty lines and lines containing known explanation keywords.
        - Attempts to identify subtitle lines, potentially by looking for quoted text (e.g., `「text」`, `"text"`) and extracting the content within the quotes.
        - If no quoted text is found on a line, and no previous subtitle lines have been extracted, the first non-explanation line is taken as a potential start of the subtitle.
        - Subsequent non-explanation lines are appended to this potential subtitle block until an empty line or an explanation keyword is encountered.
        - Markdown (`**`) is removed.
    - **Fallback Mechanism:**
        - If both the keyword heuristic and line-by-line parsing fail to extract specific content, the parser falls back to returning the first non-empty line of the raw input (with `**` removed).
        - If even that is empty, it returns the entire stripped raw input (with `**` removed) as a last resort.
    - **Logging**: The parser includes debug logging to trace its decision-making process.
- **Current Limitations/Future Improvements**:
    - The parser relies on a predefined set of keywords and simple structural assumptions. Highly varied or unexpected LLM response formats might still not be parsed perfectly.
    - More sophisticated parsing (e.g., using more advanced NLP techniques or stricter templating if models support it) could be explored if current methods prove insufficient for certain models.

### 3. Improved LLM Model Selection UI (DI: 3/5)
- **User Request**:
    - Change UI label from "LLM模型名称" to "选择LLM模型".
    - Replace the current `CTkOptionMenu` with an "input-dropdown" control (e.g., `CTkComboBox`) that allows users to type keywords to filter the model list and then select from the filtered results.
- **Rationale**: The current `CTkOptionMenu` displays all available models (e.g., 148 from `sucoiapi.com`), which can be overwhelming and includes models not relevant to text enhancement. A searchable/filterable list would improve usability.
- **Proposed UI Changes**:
    - Update the label text for the LLM model selection.
    - Replace the `CTkOptionMenu` (currently `self.llm_model_name_menu`) with a `customtkinter.CTkComboBox`.
    - The `CTkComboBox` should be configured to allow user input.
    - Implement logic in `SettingsPanel` to filter the full model list (`self.app.workflow_manager.available_llm_models`) based on the text typed into the `CTkComboBox`.
    - Dynamically update the `values` property of the `CTkComboBox` with the filtered list of model names.
- **Backend/Logic Changes (in `SettingsPanel`)**:
    - Adapt `fetch_llm_models_for_ui` and `_update_llm_model_dropdown` to work with `CTkComboBox` instead of `CTkOptionMenu`.
    - Add an event binding to the `CTkComboBox`'s input field to trigger the filtering logic whenever the text changes.
- **Considerations for "Other Model Types"**:
    - The `/v1/models` endpoint may return models for various tasks (text, image, audio, embeddings).
    - **Ideal Solution**: If the API provides model type/capability metadata, use it to pre-filter or categorize models.
    - **Pragmatic Approach**:
        - Primarily rely on user search/filtering to find relevant models.
        - Optionally, implement client-side heuristic filtering based on common keywords in model names (e.g., exclude "tts", "dall-e", "whisper", "embed") if they are clearly not for chat/text generation. This is imperfect but can reduce clutter. Apply this heuristic before populating the searchable list.
        - Document that users should be aware of model capabilities when selecting.
- **Status**: To-Do. This is a UI/UX improvement.

### 4. Import Script for LLM Context (DI: 4/5)
- **User Request**: Add an "导入剧本" (Import Script) button next to the "LLM增强" (LLM Enhancement) checkbox in the "AI及高级设置" (AI & Advanced Settings) tab. This would allow users to select a script file (e.g., .txt). The content of this script would then be sent to the LLM along with the ASR-generated subtitle segments to provide additional context, aiming to improve the accuracy and relevance of the LLM's enhancements.
- **Rationale**: Providing LLMs with relevant contextual information (like a full script) can significantly improve their ability to understand nuances, identify speakers (if applicable), use correct terminology, and generate more coherent and accurate text.
- **Proposed UI Changes (`SettingsPanel`)**:
    - Add a `CTkButton` labeled "导入剧本" near the "LLM增强" checkbox.
    - Add a `CTkLabel` or non-editable `CTkEntry` to display the name of the imported script file or a status like "未导入剧本".
    - Implement a file dialog (using `tkinter.filedialog.askopenfilename`) for selecting the script file. Supported formats could initially be `.txt`, `.md`, potentially `.srt` (extracting text).
- **Configuration & State Management**:
    - Decide if the imported script path/content is a per-session setting or should be persisted in `config.json`. For simplicity, starting with a per-session (temporary) import might be easier.
    - `SettingsPanel` would need to store the path to the selected script file and potentially read its content when processing starts.
- **Backend Implementation**:
    - `WorkflowManager`:
        - The `process_audio_to_subtitle` method would need to accept the script content (or path to be read) as a new parameter.
    - `LLMEnhancer`:
        - The `_process_segment_async` method (or a modified version if batching is implemented) needs to incorporate the script content into the prompt sent to the LLM.
        - **Prompt Engineering**: This is critical. How to best include script context?
            - Append to system prompt: "You are a subtitle editor. The following is the full script for context: [Script Content]. Now, optimize this subtitle segment: [Segment Text]".
            - Include as part of the user message.
        - **Token Limits**: This is a major challenge. Full scripts can be very long and easily exceed LLM token limits, especially if sent with every segment. Strategies needed:
            - **Summarization**: Automatically summarize the script (could use another LLM call, adding complexity/cost).
            - **Chunking/Embedding (Advanced)**: For very long scripts, more advanced techniques like RAG (Retrieval Augmented Generation) might be needed, where relevant script parts are dynamically fetched. This is likely out of scope for an initial implementation.
            - **User-guided Truncation/Selection**: Allow users to specify a maximum length for the context, or provide a way to select key scenes/parts of the script.
            - **Provide only a portion**: E.g., a few lines before and after an estimated current position in the script (if timestamps could be aligned, which is hard).
- **Error Handling**:
    - Handle cases where the script file cannot be read or is too large.
- **Status**: 代码已完成 (因LLM模型/端点不兼容问题导致测试受阻).