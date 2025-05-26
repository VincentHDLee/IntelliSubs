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
- The current hardcoded system prompts in `llm_enhancer.py` are generic. As observed, they lead to empty responses from `https://sucoiapi.com`.
- **Action**: If custom prompts are implemented, ensure the new internal defaults (if a custom one isn't set) are significantly improved or provide examples. Test prompts against a known-good service like OpenAI directly to validate prompt structure before blaming a custom API.

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

## Proposed Next Steps
1.  **Discuss & Prioritize**: Review these points. The "Customizable System Prompt" feature seems like a good first step as it directly addresses the issue of ineffective hardcoded prompts and is relatively straightforward. "Batch Processing" requires significant research into API capabilities first.
2.  **Implement "Customizable System Prompt"**:
    - Design UI for text input.
    - Update config schema.
    - Modify `LLMEnhancer` and `WorkflowManager`.
3.  **Investigate "Batch Processing"**: Research `https://sucoiapi.com` documentation for any batching capabilities. If none, this feature may need to be re-scoped or deferred.
4.  **Refine Default Prompts**: Regardless of custom prompts, try to improve the internal default prompts.
5.  **Enhance Error Reporting**: Improve UI feedback for specific HTTP errors from the LLM API.

This document will serve as a basis for these improvements.

### 3. Improved LLM Model Selection UI (DI: 3/5)
- **User Request**: Enhance the LLM model selection dropdown to be an "input then select" (filterable/searchable) list.
- **Rationale**: The current `CTkOptionMenu` displays all available models (e.g., 148 from `sucoiapi.com`), which can be overwhelming and includes models not relevant to text enhancement. A searchable/filterable list would improve usability.
- **Proposed UI Changes**:
    - Replace the current `CTkOptionMenu` for `llm_model_name` with a more advanced widget.
        - **Option A (Preferred if suitable)**: Use `customtkinter.CTkComboBox`. Investigate its capabilities for user input and dynamic filtering of its dropdown values. `CTkComboBox` allows user input and its values can be updated dynamically.
        - **Option B (If CTkComboBox is insufficient for live filtering)**: A custom composite widget (e.g., `CTkEntry` for search input, with a `CTkScrollableFrame` below it dynamically populated with filtered model names as clickable labels/buttons).
    - Implement real-time filtering of the model list based on user input in the search/entry field.
- **Backend/Logic Changes (in `SettingsPanel`)**:
    - `SettingsPanel` will need to manage the full list of models fetched from `WorkflowManager` and a separate, filtered list for display in the ComboBox's dropdown.
    - Event handling for user input in the ComboBox's entry field to trigger filtering and update the ComboBox's displayed values.
- **Considerations for "Other Model Types"**:
    - The `/v1/models` endpoint may return models for various tasks (text, image, audio, embeddings).
    - **Ideal Solution**: If the API provides model type/capability metadata, use it to pre-filter or categorize models.
    - **Pragmatic Approach**:
        - Primarily rely on user search/filtering to find relevant models.
        - Optionally, implement client-side heuristic filtering based on common keywords in model names (e.g., exclude "tts", "dall-e", "whisper", "embed") if they are clearly not for chat/text generation. This is imperfect but can reduce clutter. Apply this heuristic before populating the searchable list.
        - Document that users should be aware of model capabilities when selecting.
- **Status**: To-Do. This is a UI/UX improvement.