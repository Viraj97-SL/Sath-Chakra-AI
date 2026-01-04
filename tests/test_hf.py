import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
token = os.getenv("HF_TOKEN")

client = InferenceClient(token=token)

try:
    messages = [{"role": "user", "content": "The capital of France is"}]
    response = client.chat_completion(
        messages=messages,
        model="google/gemma-2-2b-it",
        max_tokens=10,  # Adjust as needed
        temperature=0.7  # Optional parameters
    )
    print(f"✅ Success! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")