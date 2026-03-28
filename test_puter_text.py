import puter

msg = [
    {
        "role": "user",
        "content": "Hi, what is 2+2?"
    }
]

res = puter.ChatCompletion.create(messages=msg, model="claude-3-haiku")
print("Response text:", res)
