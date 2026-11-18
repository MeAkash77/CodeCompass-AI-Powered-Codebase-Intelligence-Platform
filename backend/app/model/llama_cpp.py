from llama_cpp import Llama
from app.model.model import Model

class LlamaCppModel(Model):
    def __init__(self, model_path: str = "models/microsoft_Phi-4-mini-instruct-Q4_K_M.gguf"):
        self.llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4)

    def __call__(self, prompt: str, max_tokens: int = 128):
        output = self.llm.create_chat_completion(messages=[{
                "role": "user",
                "content": prompt
            }], max_tokens=max_tokens, stop=["</s>"], stream=False)
        return output["choices"][0]["message"]["content"] # type: ignore