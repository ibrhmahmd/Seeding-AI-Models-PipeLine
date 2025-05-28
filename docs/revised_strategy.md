# Revised Data Collection and Mapping Strategy

Based on the analysis of the provided Ollama API reference (`pasted_content.txt`) and the target API schema (`AIModelOperations`), the following strategy will be adopted for future data collection and seeding:

## 1. Primary Data Source

The primary source for model information will be the Ollama API, specifically the output of the command `ollama show --json <model_name>` executed within the sandbox environment. This provides rich, structured data directly from Ollama.

## 2. Secondary Data Source

Fields not available in the `ollama show` output will be sourced externally using web searches, prioritizing:
    - Official Ollama library pages (`ollama.com/library/...`)
    - Hugging Face model pages (`huggingface.co/...`)
    - Original research papers or official model websites.

Secondary sources will be used primarily for:
    - `description`: A concise summary of the model.
    - `releasedAt`: The official release date (if `modified_at` from Ollama is unsuitable).
    - `referenceLink`: A link to the primary source (e.g., Hugging Face page, paper).
    - `imageUrl`: A URL for the model's logo or representative image.
    - `languages`: Supported languages.

## 3. Field Mapping (Ollama JSON -> Target API)

-   **`name` (API):** Extracted from the model name used in `ollama show` (e.g., `llama3.2:1b`).
-   **`description` (API):** Sourced externally.
-   **`version` (API):** Extracted from the model tag (e.g., `1b` from `llama3.2:1b`).
-   **`size` (API):** Map from `details.size` (file size, e.g., `668 MiB`).
-   **`releasedAt` (API):** Use `modified_at` if suitable, otherwise source externally.
-   **`referenceLink` (API):** Use `details.project_url` if available, otherwise source externally.
-   **`imageUrl` (API):** Sourced externally.
-   **`fromOllama` (API):** Set to `false` (as requested).
-   **`license` (API):** Extract license name/identifier from the full `license` text (e.g., "LLAMA 3.2 COMMUNITY LICENSE AGREEMENT").
-   **`template` (API):** Map directly from `template`.
-   **`modelFile` (API):** Map directly from `modelfile`.
-   **`digest` (API):** Map from `details.digest`.
-   **`format` (API):** Map from `details.format`.
-   **`parameterSize` (API):** Map from `details.parameter_size` (e.g., `1B`).
-   **`quantizationLevel` (API):** Map from `details.quantization_level` (e.g., `Q8_0`).
-   **`parentModel` (API):** Map from `details.parent_model`.
-   **`family` (API):** Map from `details.family`.
-   **`families` (API):** Map from `details.families` (array).
-   **`languages` (API):** Sourced externally (array).
-   **`architecture` (API):** Map from `details.model_info['general.architecture']`.
-   **`fileType` (API):** Map from `details.model_info['general.file_type']` (convert to integer).
-   **`parameterCount` (API):** Map from `details.model_info['general.parameter_count']` (convert to integer).
-   **`quantizationVersion` (API):** Map from `details.model_info['general.quantization_version']` (convert to integer).
-   **`sizeLabel` (API):** Derive from `parameterSize` (e.g., "1B", "7B", "70B").
-   **`modelType` (API):** Derive from `family` or `architecture` (e.g., "Language Model", "Multimodal").
-   **`tags` (API):** Derive relevant tags (family, size, quantization, capabilities like "completion", "tools", license type) from collected data and map to existing `tagId`s from `/home/ubuntu/created_tag_ids.json`. New necessary tags will be created.

## 4. Implementation

A Python script will be developed to:
    a. Accept a model name (e.g., `llama3:latest`).
    b. Execute `ollama show --json <model_name>`.
    c. Parse the JSON output.
    d. Perform web searches for supplementary data.
    e. Apply the mapping and transformations defined above.
    f. Derive and map tags.
    g. Generate the final JSON payload conforming to the `AIModelOperations` API schema.

This script will form the basis for the realigned data extraction and seeding process in the next step.

