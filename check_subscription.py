import os
from pyrogram import Client

CHANNEL_IDS = list(map(int, os.getenv("REQUIRED_CHANNELS").split(",")))

async def check_user_subscribed(client: Client, user_id: int) -> bool:
    for ch_id in CHANNEL_IDS:
        try:
            member = await client.get_chat_member(ch_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True
