import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

# Configuration to run your server file
server_params = StdioServerParameters(
    command="python",
    args=["browser_server.py"], # Must match your filename
)

async def test_links():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # --- TEST 1: Rooter ---
            print("\n🔍 Testing Rooter...")
            result = await session.call_tool("scrape_product", arguments={
                "url": "https://shop.rooter.gg/product/valorant-points"
            })
            print(result.content[0].text)

            # --- TEST 2: Amazon ---
            print("\n🔍 Testing Amazon...")
            result = await session.call_tool("scrape_product", arguments={
                "url": "https://www.amazon.in/s?k=valorant+points"
            })
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_links())