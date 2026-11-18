from app.model.model import Model
from google import genai
from google.genai import types

class GeminiModel(Model):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        self.client = genai.Client(credentials=api_key)
        self.model_name = model_name

    def __call__(self, prompt: str, max_tokens: int = 128):
        response = self.client.models.generate_content(
            model=self.model_name, 
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens)
        )
        return response.text
