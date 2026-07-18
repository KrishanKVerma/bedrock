"""What models does this Cerebras key have access to?"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("CEREBRAS_API_KEY"), base_url="https://api.cerebras.ai/v1")
for m in client.models.list().data:
    print(m.id)