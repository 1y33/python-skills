## Task

Write a small inference engine in Python that runs GPT-2 small from the Hugging Face safetensors weights and generates text from a prompt. NumPy is fine, no torch or transformers. It should stream tokens as they are generated and not be painfully slow on long outputs.

## Follow-up (send after the first turn is done and committed)

Now make it run a Llama-style model too (RMSNorm, rotary embeddings, SwiGLU, grouped-query attention), for example TinyLlama 1.1B, and add top-p sampling.
