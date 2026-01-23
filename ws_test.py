import asyncio
import websockets
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsInBlcm1zIjpbInRvb2w6cmVxdWVzdCIsImNoYXQ6c2VuZCIsImhlYWx0aDpyZWFkIiwiY2hhdDpyZWFkIiwibWV0cmljczpyZWFkIiwiYWdlbnQ6cmVhZCIsInRvb2w6cmVqZWN0IiwidG9vbDphcHByb3ZlIiwiYWdlbnQ6d3JpdGUiLCJ0b29sOnJlYWQiLCJjb25maWc6cmVsb2FkIiwidG9vbDpleGVjdXRlIiwiZG9tYWluOnJlYWQiXSwiaWF0IjoxNzY5MDk4MjAxLCJleHAiOjE3NjkxODQ2MDF9.0kIRlSyuSodHhBqz_kBjsZBS2QBeOUzv2O8-sTqUGE8"

async def test_ws():
    uri = f"ws://localhost/ws?token={TOKEN}"
    print(f"Connecting to {uri}")
    async with websockets.connect(uri, origin="http://localhost") as websocket:
        print("Connected!")
        await websocket.send(json.dumps({"type": "PING"}))
        print("Sent PING")
        response = await websocket.recv()
        print(f"Received: {response}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test_ws())
