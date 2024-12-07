# firestore-read MCP Server

A Claude MCP server that enables Claude to read and interact with your existing Firestore collections directly.

More future updates will likely be coming soon, for my personal use, or if others are very keen on seeing updates here. I am doing this personally because when developing ReactJS apps, I often have to face the hustle of continuously having to show Claude-Sonnet-3.5 what my current Firestore collections and document fiels looks like, else it will hallucinate, and always make weird assumptions and just ruins everything. Hence, this allows programmers to swiftly allow Claude-3.5 to readily read your firestore collections easily (given everything is set to public, idk this will likely only be improved in the future if I really need to or that I get requests).

## Features

This server allows Claude to:
- List all collections in your Firestore database
- Read documents from any collection
- Create new documents in existing collections
- Handle complex Firestore data types including timestamps and document references

## Tools

The server implements three main tools:

### 1. list-collections
Lists all collections in the Firestore database.
- No parameters required
- Returns an array of collection names

### 2. get-collection
Retrieves all documents from a specified collection.
- Required parameter: `collection` (string)
- Returns array of documents with their IDs and data

### 3. create-document
Creates a new document in a specified collection.
- Required parameters: 
  - `collection` (string)
  - `document_data` (object)
- Returns confirmation message with new document ID

## Configuration

### Environment Variables

The server requires two environment variables:
```bash
FIREBASE_API_KEY=your-firebase-web-api-key
FIREBASE_PROJECT_ID=your-firebase-project-id
```

Note: These are web client credentials and are safe to expose in client-side code.

## Installation

### Prerequisites
- Python 3.11 or higher
- `uv` package manager

### Dependencies
```bash
uv pip install firebase-admin
uv pip install python-dotenv
```

### Claude Desktop Configuration

Add this to your Claude Desktop config file:

#### MacOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Windows
Location: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "firestore-read": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/firestore-read",
        "run",
        "firestore-read"
      ],
      "env": {
        "FIREBASE_API_KEY": "your-firebase-web-api-key",
        "FIREBASE_PROJECT_ID": "your-firebase-project-id"
      }
    }
  }
}
```

## Usage Examples

Here are some example interactions with Claude using this server:

### Listing Collections
```
Human: List all collections in my Firestore database.

Claude: I'll list all collections in your database:
[
  {
    "name": "users"
  },
  {
    "name": "projects"
  },
  {
    "name": "tasks"
  }
]
```

### Reading Documents
```
Human: Show me the documents in the users collection.

Claude: Here are the documents from the users collection:
[
  {
    "id": "user123",
    "data": {
      "name": "John Doe",
      "email": "john@example.com",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  }
]
```

### Creating Documents
```
Human: Create a new test document.

Claude: I'll create a new test document:
Created new document with ID abc123 in 'test'
```

## Development

### Debugging

For debugging, you can use the MCP Inspector. Install and run it using:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/your/firestore-read run firestore-read
```

### Error Handling

The server includes error handling for:
- Firebase initialization failures
- Invalid collection names
- Document creation errors
- Invalid data types
- Missing environment variables

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
