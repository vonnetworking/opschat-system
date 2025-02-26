import os
from qdrant_client import QdrantClient

# Get Qdrant connection info from environment variables or use defaults
QDRANT_HOST = os.environ.get("QDRANT_HOST", "romantic_solomon")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))

print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

print(client.get_collections())

collection_name = 'opschat_data'
collection_info = client.get_collection(collection_name)
print(f"Collection info: {collection_info}")

# Get points with vectors included
scroll_response = client.scroll(
    collection_name="opschat_data",
    limit=100,
    with_vectors=True,  # This is key - we need to explicitly request vectors
    with_payload=True,   # Get payload too
)

# Look at the vectors and payloads
for point in scroll_response[0]:  # [0] contains points, [1] contains next_page_offset
    print(f"Payload: {point.payload}")

print(f"\n\nVector dimension: {len(scroll_response[0][0].vector)}")