from config import REQUIRED_CHANNELS
from pyrogram.errors import UserNotParticipant

async def check_user_subscribed(client, user_id):
    for channel_id in REQUIRED_CHANNELS:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status in ("left", "kicked"):
                return False
        except UserNotParticipant:
            return False
        except:
            return False
    return True
