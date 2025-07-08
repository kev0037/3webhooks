import aiohttp
import asyncio
from aiohttp import web
import random
from datetime import datetime, timezone

# --- CONFIGURATION ---
DEALS_WEBHOOK = "https://discord.com/api/webhooks/1392240876146655262/YgnQOEvirH_A9SJf0RC5KSquSs-cPxaFoA3fxVDk5YJMx-OQgQphiBD8mJQje4IAYc_Y"  # Replace with your actual webhook
MEME_WEBHOOK = "https://discord.com/api/webhooks/1392238279176224898/6owmLQrIZ2xA1tBEsPkrCfVnPjnkodiqphE_x8KnO0EhDmf0WNKbjrI4MgRLOicxThZX"
NSFW_WEBHOOK = "https://discord.com/api/webhooks/1392234905546657843/7hyRQ8ucTK9wJX9uITFE4Z4vh9B_KJzGlk9pGZVY86fu31kt59VHILMKZyQ5y4Evw_MW"

# Stores
STORES = {
    "1": {"name": "Steam"},
    "13": {"name": "Epic Games"}
}

# Meme subreddits
SUBREDDITS = ["memes", "dankmemes"]

# NSFW APIs
NSFW_URLS = [
    "https://nekobot.xyz/api/image?type=boobs",
    "https://nekobot.xyz/api/image?type=hboobs",
    "https://nekobot.xyz/api/image?type=4k"
]


# --- UTILITIES ---
def get_store_url(deal):
    store_id = deal.get("storeID")
    if store_id == "1":
        steam_app_id = deal.get("steamAppID")
        if steam_app_id and steam_app_id != "0":
            return f"https://store.steampowered.com/app/{steam_app_id}"
    return f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"


# --- DEALS TASK ---
async def fetch_deals(session, store_id):
    url = f"https://www.cheapshark.com/api/1.0/deals?storeID={store_id}&upperPrice=30&pageSize=20"
    try:
        async with session.get(url) as resp:
            return await resp.json()
    except Exception as e:
        print(f"[DEALS] Error: {e}")
        return []


async def send_deal(session, deal):
    store_info = STORES.get(deal["storeID"], {"name": "Unknown"})
    store_url = get_store_url(deal)

    embed = {
        "title": deal["title"],
        "color": 0x23272A,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thumbnail": {"url": deal["thumb"]},
        "author": {"name": store_info["name"]},
        "fields": [
            {"name": "Sale Price", "value": f"${deal['salePrice']}", "inline": True},
            {"name": "Normal Price", "value": f"${deal['normalPrice']}", "inline": True},
            {"name": "Savings", "value": f"{float(deal['savings']):.2f}%", "inline": True},
            {"name": "Open in Browser", "value": f"[Click here]({store_url})", "inline": False}
        ]
    }

    payload = {
        "username": "Deal Bot",
        "avatar_url": "https://i.postimg.cc/zXJv4jSm/1071de2e186547f2e509dfd031fcf86a.png",
        "embeds": [embed]
    }

    async with session.post(DEALS_WEBHOOK, json=payload) as resp:
        print(f"[DEALS] Sent: {deal['title']} - Status: {resp.status}")


async def deal_loop(session):
    posted = set()
    while True:
        all_deals = []
        for store in STORES:
            deals = await fetch_deals(session, store)
            all_deals.extend(deals)
        new = [d for d in all_deals if d["dealID"] not in posted]
        if new:
            deal = random.choice(new)
            await send_deal(session, deal)
            posted.add(deal["dealID"])
        else:
            print("[DEALS] No new deals.")
        await asyncio.sleep(60)


# --- MEME TASK ---
async def fetch_meme(session):
    subreddit = random.choice(SUBREDDITS)
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
    headers = {"User-Agent": "DiscordWebhookMemeBot"}

    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            posts = data["data"]["children"]
            images = [p["data"] for p in posts if p["data"].get("post_hint") == "image"]
            if images:
                meme = random.choice(images)
                return {
                    "title": meme["title"],
                    "image_url": meme["url"],
                    "post_url": "https://reddit.com" + meme["permalink"]
                }
    except Exception as e:
        print(f"[MEME] Error: {e}")
    return None


async def send_meme(session, meme):
    if not meme: return

    embed = {
        "title": meme["title"],
        "url": meme["post_url"],
        "color": 0x2f3136,
        "image": {"url": meme["image_url"]},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "username": "Meme Bot",
        "avatar_url": "https://i.postimg.cc/VN2z6LcP/IMG-2004.jpg",
        "embeds": [embed]
    }

    async with session.post(MEME_WEBHOOK, json=payload) as resp:
        print(f"[MEME] Sent: {meme['title']} - Status: {resp.status}")


async def meme_loop(session):
    while True:
        meme = await fetch_meme(session)
        await send_meme(session, meme)
        await asyncio.sleep(60)


# --- NSFW TASK ---
async def fetch_nsfw(session):
    url = random.choice(NSFW_URLS)
    try:
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get("message")
    except Exception as e:
        print(f"[NSFW] Fetch error: {e}")
        return None


async def send_nsfw(session, img_url):
    if not img_url: return

    embed = {
        "title": "💖 Here's something spicy!",
        "description": "Fresh NSFW drop 🔞",
        "color": 0xE91E63,
        "image": {"url": img_url},
        "footer": {"text": "AutoPoster by @raydongg"},
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {
        "username": "NSFW",
        "avatar_url": "https://i.postimg.cc/PxbPZ8yk/1159e3a020be04eede0cb5506b3517da.jpg",
        "embeds": [embed]
    }

    async with session.post(NSFW_WEBHOOK, json=payload) as resp:
        print(f"[NSFW] Sent - Status: {resp.status}")


async def nsfw_loop(session):
    while True:
        image = await fetch_nsfw(session)
        await send_nsfw(session, image)
        await asyncio.sleep(30)


# --- DUMMY SERVER (REQUIRED BY RENDER) ---
async def index(request):
    return web.Response(text="Bot is running!", content_type="text/plain")


async def run_bot():
    async with aiohttp.ClientSession() as session:
        tasks = [
            deal_loop(session),
            meme_loop(session),
            nsfw_loop(session)
        ]
        await asyncio.gather(*tasks)


def start_server():
    app = web.Application()
    app.router.add_get("/", index)
    return app


if __name__ == "__main__":
    async def main():
        # Start background tasks
        asyncio.create_task(run_bot())

        # Start dummy server
        app = start_server()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()
        print("======= Serving on http://0.0.0.0:8080 =======")

        # Keep running
        while True:
            await asyncio.sleep(3600)

    asyncio.run(main())
