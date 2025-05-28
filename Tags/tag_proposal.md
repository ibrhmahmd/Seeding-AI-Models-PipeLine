# Proposed Tags for AI Model Database

Based on our discussion and research into common AI model classifications, I propose the following categories and example tags to ensure a diverse and well-structured database. These tags aim to cover key aspects like the model's primary function (task), the type of data it handles (modality), its underlying structure (architecture/family), its size, the languages it supports, and its usage rights (license).

## Modality Tags

These tags describe the type of data the AI model is designed to process or generate. Capturing modality helps users find models suited for specific input or output types.

*   **Text:** For models primarily focused on processing or generating natural language text.
*   **Code:** For models specialized in understanding, generating, or completing programming code.
*   **Image:** For models that analyze, generate, or manipulate images.
*   **Audio:** For models dealing with speech recognition, audio generation, or sound analysis.
*   **Video:** For models designed for video analysis, generation, or processing.
*   **Multimodal:** For versatile models capable of handling multiple data types simultaneously (e.g., text and images).

## Task Tags

Task tags specify the primary application or function the model is intended for. This allows users to filter models based on the specific problem they want to solve.

*   **Text Generation:** Models creating human-like text (e.g., chatbots, story writing).
*   **Code Generation:** Models assisting with writing or completing software code.
*   **Image Generation:** Models creating images from text descriptions or other inputs.
*   **Classification:** Models assigning predefined categories to input data (e.g., sentiment analysis, spam detection).
*   **Translation:** Models converting text from one language to another.
*   **Summarization:** Models condensing longer texts into shorter summaries.
*   **Question Answering:** Models providing answers to questions based on given context or learned knowledge.
*   **Object Detection:** Models identifying and locating objects within images or videos.
*   **Feature Extraction:** Models identifying key features or embeddings from data.
*   **Recommendation:** Models suggesting items or content based on user preferences or data patterns.

## Architecture/Family Tags

These tags denote the underlying technical architecture or the family the model belongs to. This is useful for users interested in specific model lineages or technical characteristics.

*   **Transformer:** A foundational architecture for many modern NLP and other models.
*   **CNN (Convolutional Neural Network):** Commonly used for image processing tasks.
*   **RNN (Recurrent Neural Network):** Suitable for sequential data like text or time series.
*   **LSTM (Long Short-Term Memory):** An advanced type of RNN for handling long sequences.
*   **GAN (Generative Adversarial Network):** Often used for generative tasks, especially image generation.
*   **BERT Family:** Models based on Google's BERT architecture.
*   **GPT Family:** Models based on OpenAI's GPT architecture.
*   **Llama Family:** Models developed by Meta.
*   **Mistral Family:** Models developed by Mistral AI.
*   **Qwen Family:** Models developed by Alibaba Cloud.
*   **Gemma Family:** Models developed by Google.
*   **Phi Family:** Small language models developed by Microsoft.

## Size (Parameter Count) Tags

Size tags give an indication of the model's complexity and resource requirements, typically measured by the number of parameters. We can use ranges for easier categorization.

*   **<1B Parameters:** Very small models.
*   **1B-3B Parameters:** Small models.
*   **3B-7B Parameters:** Medium-small models.
*   **7B-13B Parameters:** Medium models.
*   **13B-30B Parameters:** Medium-large models.
*   **30B-70B Parameters:** Large models.
*   **>70B Parameters:** Very large models.

## Quantization Tags

Quantization refers to techniques used to reduce the model's size and computational cost, often affecting performance. These tags indicate the format or level of quantization.

*   **GGUF:** A popular format for running models on CPUs/GPUs.
*   **AWQ (Activation-aware Weight Quantization):** A specific quantization technique.
*   **GPTQ:** Another common quantization method.
*   **4-bit:** Indicates 4-bit quantization.
*   **8-bit:** Indicates 8-bit quantization.
*   **FP16 / BF16:** Indicates 16-bit floating-point precision (less compressed).
*   **FP32:** Indicates standard 32-bit floating-point precision (unquantized).

## License Tags

License tags are crucial for understanding the permitted usage of the model (e.g., commercial use, research only).

*   **Apache 2.0:** A permissive open-source license.
*   **MIT:** Another permissive open-source license.
*   **Llama 2 License:** Specific license for Llama 2 models.
*   **Gemma License:** Specific license for Gemma models.
*   **Mistral License:** Specific license associated with Mistral models (often Apache 2.0).
*   **OpenRAIL:** Responsible AI Licenses.
*   **CC-BY-SA-4.0:** Creative Commons Attribution-ShareAlike license.
*   **Commercial Use Allowed:** A general tag indicating commercial viability.
*   **Research Only:** Models restricted to non-commercial research purposes.

## Language Tags

These tags specify the primary language(s) the model was trained on or is proficient in.

*   **English**
*   **Chinese**
*   **Spanish**
*   **French**
*   **German**
*   **Japanese**
*   **Korean**
*   **Multilingual:** Models designed to handle multiple languages.

This list provides a solid foundation. We can refine it further based on the specific models we find during the data collection phase. Please review this proposal and let me know if these categories and examples align with your vision for the database.
