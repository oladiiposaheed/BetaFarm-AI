import requests

# Test health
print("Testing health...")
r = requests.get('http://localhost:8001/health')
print(f"Health: {r.status_code} - {r.text}")

# Test predict with a real image (update path)
print("\nTesting predict...")
try:
    with open('C:/Users/USER/Downloads/test_leaf.jpg', 'rb') as f:
        files = {'image': ('leaf.jpg', f, 'image/jpeg')}
        r = requests.post('http://localhost:8001/predict', files=files)
        print(f"Predict: {r.status_code}")
        print(f"Response: {r.text}")
except FileNotFoundError:
    print("Please provide a valid image path")