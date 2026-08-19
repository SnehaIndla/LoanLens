import ollama


response = ollama.chat(
    model="qwen2:7b",
    messages=[
        {
            "role": "user",
            "content": (
                "Explain in one sentence why "
                "loan documents should be cross-checked."
            )
        }
    ]
)


print("\nAI RESPONSE:")
print(response["message"]["content"])