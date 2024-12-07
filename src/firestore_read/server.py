import asyncio
import json
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os

# Initialize Firebase with web config
config = {
    'apiKey': os.environ.get('FIREBASE_API_KEY'),
    'projectId': os.environ.get('FIREBASE_PROJECT_ID')
}

try:
    app = initialize_app(options=config)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {str(e)}")
    db = None

# Create single server instance
server = Server("firestore-read")

class FirestoreEncoder(json.JSONEncoder):
    def default(self, obj):
        from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
        
        if isinstance(obj, DatetimeWithNanoseconds):
            return obj.isoformat()
        elif hasattr(obj, 'path'):
            return str(obj.path)
        return super().default(obj)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Firestore tools."""
    return [
        types.Tool(
            name="list-collections",
            description="List all collections in the database",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        ),
        types.Tool(
            name="get-collection",
            description="Get all documents from a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string"}
                },
                "required": ["collection"]
            },
        ),
        types.Tool(
            name="create-document",
            description="Create a new document in an existing collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string"},
                    "document_data": {"type": "object"}
                },
                "required": ["collection", "document_data"]
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool execution."""
    if not db:
        return [
            types.TextContent(
                type="text",
                text="Error: Firebase not properly initialized"
            )
        ]

    # Remove or modify this check for list-collections
    if not arguments and name != "list-collections":  # <-- Add this condition
        return [
            types.TextContent(
                type="text",
                text="Error: Missing arguments"
            )
        ]

    try:
        if name == "list-collections":
            collections = db.collections()
            result = [{"name": col.id} for col in collections]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]

        elif name == "get-collection":
            collection = arguments.get("collection")
            docs = db.collection(collection).stream()
            result = []
            for doc in docs:
                result.append({
                    "id": doc.id,
                    "data": doc.to_dict()
                })
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, cls=FirestoreEncoder)
                )
            ]

        elif name == "create-document":
            collection = arguments.get("collection")
            document_data = arguments.get("document_data")
            
            # Add new document to collection
            doc_ref = db.collection(collection).document()
            doc_ref.set(document_data)
            return [
                types.TextContent(
                    type="text",
                    text=f"Created new document with ID {doc_ref.id} in '{collection}'"
                )
            ]

        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Unknown tool: {name}"
                )
            ]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )
        ]

async def main():
    if not db:
        print("Warning: Firebase not initialized. Some features may not work.")
        
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="firestore-read",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())