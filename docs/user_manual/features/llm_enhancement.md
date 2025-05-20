# Feature: LLM (Large Language Model) Enhancement

智字幕 (IntelliSubs) offers an optional feature to enhance the generated subtitle text using a Large Language Model (LLM). This can help improve punctuation, grammar, clarity, and overall naturalness of the Japanese text.

## What LLM Enhancement Does

When enabled, after the initial ASR transcription and basic normalization, the text segments are sent to an LLM for further refinement. The LLM can perform tasks such as:

*   **Intelligent Punctuation:** Adding or correcting Japanese punctuation (「。」, 「、」, 「？」, 「！」) more accurately than rule-based systems, based on contextual understanding.
*   **Grammar Correction:** Fixing grammatical errors in the transcribed text.
*   **Text潤色 (Polishing/Smoothing):** Rephrasing awkward sentences to make them sound more natural and flow better for subtitles.
*   **Clarity Improvement:** Making the text easier to understand.
*   **(Potential Future) Formality/Style Adjustment:** For example, adjusting a sentence to a more polite form (敬語) if the LLM is prompted and capable.

## Enabling and Disabling LLM Enhancement

You can typically enable or disable this feature in the application's **Settings** or **Preferences** panel.

*   Look for a checkbox or toggle switch labeled something like **"启用LLM增强" (Enable LLM Enhancement)**.
*   **Default:** This feature might be disabled by default because it usually requires an active internet connection and an API key for an LLM service, and it adds to the processing time.

## LLM Provider and API Key Configuration

IntelliSubs aims to support LLMs accessible via an OpenAI-compatible API.

*   **LLM Provider:** The settings might show which provider or API type is being used (e.g., "OpenAI API").
*   **API Key:** To use LLM enhancement with services like OpenAI's GPT models, you will need to provide your own **API Key**.
    1.  Obtain an API key from your chosen LLM provider (e.g., from your OpenAI account dashboard).
    2.  In IntelliSubs's settings, find the field labeled **"LLM API Key"** (or similar).
    3.  Carefully paste your API key into this field.
    *   **Security Note:** Your API key is sensitive. IntelliSubs will store it locally in its configuration file. Ensure your computer is secure. The application will not share your API key, but be mindful of who has access to your computer or configuration files.
*   **LLM Model Name:** You might be able to select a specific LLM model (e.g., `gpt-3.5-turbo`, `gpt-4`, etc., if supported and you have access). Different models have different capabilities, costs, and speed. The application will have a default model.
*   **(Advanced) Base URL:** For users with custom OpenAI-compatible API endpoints (e.g., self-hosted models via LocalAI, or other proxy services), an option to specify a "Base URL" might be available.

## Considerations When Using LLM Enhancement

*   **Internet Connection:** Most LLM services are cloud-based and require an active internet connection.
*   **Processing Time:** Sending text to an LLM and waiting for a response adds to the overall subtitle generation time.
*   **Cost:** Using commercial LLM APIs (like OpenAI's) incurs costs based on your usage (number of tokens processed). Be aware of your LLM provider's pricing.
*   **Quality Variability:** While LLMs are powerful, the quality of enhancement can vary depending on the model, the input text quality, and the specific instructions given to the LLM. Sometimes, LLM edits might not be perfect or might alter the original meaning unintentionally. Always review LLM-enhanced subtitles.
*   **Rate Limits:** API services often have rate limits. If you process a very large amount of text quickly, you might encounter these limits.

## When to Use LLM Enhancement

*   When you need the highest possible quality for your Japanese subtitles.
*   When the raw ASR output contains noticeable grammatical errors or awkward phrasing.
*   When precise and contextually-aware punctuation is crucial.
*   If you are willing to accept slightly longer processing times and potential API costs for improved text quality.

---

Experiment with this feature to see if it benefits your specific workflow and content type. Always preview the results carefully.