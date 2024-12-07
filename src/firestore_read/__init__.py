from . import server

def main():
    import asyncio
    try:
        asyncio.run(server.main())
    except Exception as e:
        print(f"Error running server: {e}")