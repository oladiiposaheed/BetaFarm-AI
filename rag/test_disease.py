# from pathlib import Path
# import requests

# downloads = Path.home() / 'Downloads'
# jpg_files = list(downloads.glob('*.jpg'))

# if not jpg_files:
#     print("No JPG files found in Downloads folder")
# else:
#     image_path = jpg_files[0]
#     print(f"Testing: {image_path.name}")
#     print(f"Size: {image_path.stat().st_size} bytes")
    
#     with open(image_path, 'rb') as f:
#         response = requests.post('http://localhost:8001/predict', files={'image': f})
#         print(f"\nStatus: {response.status_code}")
        
#         if response.status_code == 200:
#             result = response.json()
#             print(f"Disease: {result.get('disease_name')}")
#             print(f"Confidence: {result.get('confidence')}%")
#             print(f"Health: {result.get('health_status')}")
#         else:
#             print(f"Error: {response.text}")


from huggingface_hub import list_repo_files

repo_id = "oladiiposaheed/betafarm-pdfs"

files = list_repo_files(repo_id, repo_type="dataset")

print(f"Total files: {len(files)}")
print("\nFiles uploaded:")
for f in files:
    print(f"  - {f}")