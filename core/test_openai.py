import os

from dotenv import load_dotenv


load_dotenv()


api_key = os.getenv(
    "OPENAI_API_KEY"
)


if api_key:

    print("✓ OPENAI_API_KEY loaded")

else:

    print("⚠ OPENAI_API_KEY not found")