# Create test_rag.py
import requests

response = requests.post(
    'http://localhost:8002/api/v1/chat',
    json={'question': 'How to treat Tomato Early Blight?', 'top_k': 5}
)
print(f"Length: {len(response.json()['answer'])}")
print(response.json()['answer'])