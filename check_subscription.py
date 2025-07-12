from pyrogram.errors import UserNotParticipant

CHANNELS = ["@BoxOfficeMoviiie", "@BoxOffice_Irani", "@BoxOffice_Animation", "@BoxOfficeGoftegu"]

async def check_user_subscribed(client, user_id):
    for channel in CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except UserNotParticipant:
            return False
        except Exception:
            return False
    return True
