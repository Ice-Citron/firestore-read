import asyncio
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.credentials import Certificate

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

# Read Firebase config from environment variables
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.environ.get("FIREBASE_APP_ID"),
    "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID")
}

# Initialize Firebase
app = firebase_admin.initialize_app(credentials.ApplicationDefault(), FIREBASE_CONFIG)
db = firestore.client(app)

server = Server("firestore-read")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Firestore tools."""
    return [
        types.Tool(
            name="query-collection",
            description="Query documents from a collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string"},
                    "where": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 3
                        }
                    },
                    "limit": {"type": "integer"},
                    "orderBy": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "direction": {"type": "string", "enum": ["asc", "desc"]}
                        }
                    }
                },
                "required": ["collection"]
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution."""
    if not arguments:
        raise ValueError("Missing arguments")

    if name == "query-collection":
        collection = arguments.get("collection")
        where_filters = arguments.get("where", [])
        limit = arguments.get("limit")
        order_by = arguments.get("orderBy")

        # Build query
        query = db.collection(collection)
        
        # Apply where filters
        for field, op, value in where_filters:
            query = query.where(field, op, value)
        
        # Apply ordering
        if order_by:
            query = query.order_by(
                order_by["field"], 
                direction=firestore.Query.DESCENDING 
                if order_by["direction"] == "desc" 
                else firestore.Query.ASCENDING
            )
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute query
        try:
            docs = query.stream()
            result = []
            for doc in docs:
                result.append({
                    "id": doc.id,
                    "data": doc.to_dict()
                })

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error querying collection: {str(e)}"
                )
            ]

    else:
        raise ValueError(f"Unknown tool: {name}")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List all collections as resources."""
    try:
        collections = db.collections()
        return [
            types.Resource(
                uri=AnyUrl(f"firestore://{collection.id}"),
                name=f"Collection: {collection.id}",
                description=f"Firestore collection {collection.id}",
                mimeType="application/json",
            )
            for collection in collections
        ]
    except Exception as e:
        print(f"Error listing collections: {str(e)}")
        return []

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read documents from a collection."""
    if uri.scheme != "firestore":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    collection_id = uri.netloc
    docs = db.collection(collection_id).stream()
    result = []
    for doc in docs:
        result.append({
            "id": doc.id,
            "data": doc.to_dict()
        })
    return json.dumps(result, indent=2)

async def main():
    # Verify required environment variables are set
    required_vars = [
        "FIREBASE_API_KEY",
        "FIREBASE_AUTH_DOMAIN",
        "FIREBASE_PROJECT_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return

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