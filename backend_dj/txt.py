import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Test with a dummy file
        files = {'image': ('test.jpg', b'test', 'image/jpeg')}
        response = await client.post('http://localhost:8001/predict', files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

asyncio.run(test())