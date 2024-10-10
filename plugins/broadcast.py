from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from plugins.dbusers import db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
import asyncio
import datetime
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} - Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return False, "Error"

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_command(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply_text(
        text='Broadcasting your messages...'
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0
    success = 0
    async for user in users:
        if 'id' in user:
            pti, sh = await broadcast_messages(int(user['id']), b_msg)
            if pti:
                success += 1
            elif pti == False:
                if sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
            done += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")    
        else:
            done += 1
            failed += 1
            if not done % 20:
                await sts.edit(f"Broadcast in progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")    
    
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}")


# Admin-only commands
@Client.on_message(filters.command("sent") & filters.user(ADMINS))
async def sent_command(bot, message):
    user_id = message.command[1]
    if not user_id.isdigit():
        await message.reply_text("Invalid user ID.")
        return
    user_id = int(user_id)

    inline_buttons = [
        [InlineKeyboardButton("ᴀᴘᴘʀᴏᴠᴇ  ᴘʀᴇᴍɪᴜᴍ💸", f"approve_{user_id}")], 
        [InlineKeyboardButton("ᴅᴇᴄʟɪɴᴇ  ᴅᴏɴᴀᴛɪᴏɴ❌", f"decline_{user_id}")],
        [InlineKeyboardButton("ᴀᴘᴘʀᴏᴠᴇ  ᴅᴏɴᴀᴛɪᴏɴ💖", f"donate_{user_id}")],
        [InlineKeyboardButton("ʙᴀɴ  ᴡᴀʀɴɪɴɢ⚠️", f"warning_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_buttons)
    
    await message.reply_text("**sᴇʟᴇᴄᴛ  ᴀᴄᴛɪᴏɴ  ғʀᴏᴍ  ʙᴇʟᴏᴡ  ʙᴜᴛᴛᴏɴs**\n\nchoose carefully, you only have one chance", reply_markup=reply_markup)

# Admin-only callback handlers
@Client.on_callback_query(filters.regex(r"approve_\d+") & filters.user(ADMINS))
async def approve_callback(client, callback_query):
    user_id = int(callback_query.data.split('_')[1])
    await callback_query.message.edit_text("**ᴘʀᴇᴍɪᴜᴍ  ᴄᴏᴍᴍᴀɴᴅ  ɢɪᴠᴇɴ  ᴛᴏ  ᴜsᴇʀs**")
    await client.send_message(user_id, "**ᴠᴇʀɪғɪᴇᴅ ☑️  ᴛʜᴀɴᴋ   ʏᴏᴜ  ғᴏʀ  ᴅᴏɴᴀᴛɪᴏɴ🎉  ʏᴏᴜʀ  ᴅᴏɴᴀᴛɪᴏɴ  ʀᴇᴀʟʟʏ  ʜᴇʟᴘ  ᴜs  ᴀ  ʟᴏᴛ** \n🤞🏼Hope  we  get  your  donation  again 😀\n\n**ᴀ  ʀᴇᴡᴀʀᴅ🎁  ғᴏʀ  ʏᴏᴜ  ᴄʟɪᴄᴋ  ʙᴇʟᴏᴡ**.[🎊](https://envs.sh/nt3.mp4) \nbutton not open ? you are ineligible for rewards", reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅs🥳", callback_data="rewards")
    ]]))
    
@Client.on_callback_query(filters.regex(r"donate_\d+") & filters.user(ADMINS))
async def donation_callback(client, callback_query):
    user_id = int(callback_query.data.split('_')[1])
    await callback_query.message.edit_text("**ᴅᴏɴᴀᴛɪᴏɴ  ᴀᴘᴘʀᴏᴠᴇᴅ  ᴛᴏ  ᴛʜᴀᴛ  ᴜsᴇʀs**")
    await client.send_message(user_id, "**ᴠᴇʀɪғɪᴇᴅ ☑️  ᴛʜᴀɴᴋ   ʏᴏᴜ  ғᴏʀ  ᴅᴏɴᴀᴛɪᴏɴ🎉  ʏᴏᴜʀ  ᴅᴏɴᴀᴛɪᴏɴ  ʀᴇᴀʟʟʏ  ʜᴇʟᴘ  ᴜs  ᴀ  ʟᴏᴛ** \n🤞🏼Hope  we  get  your  donation  again 😀\n\n**ᴀ  ʀᴇᴡᴀʀᴅ🎁  ғᴏʀ  ʏᴏᴜ  ᴄʟɪᴄᴋ  ʙᴇʟᴏᴡ**.[🎊](https://envs.sh/nt3.mp4) \nbutton not open ? you are ineligible for rewards", reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʀᴇᴡᴀʀᴅs🥳", callback_data="reward")
    ]]))


@Client.on_callback_query(filters.regex(r"decline_\d+") & filters.user(ADMINS))
async def decline_callback(client, callback_query):
    user_id = int(callback_query.data.split('_')[1])
    await callback_query.message.edit_text("**ᴅᴏɴᴀᴛɪᴏɴ ᴅᴇᴄʟɪɴᴇ ғᴏʀ ᴛʜᴀᴛ ᴜsᴇʀs**")
    await client.send_message(user_id, "**ᴅᴏɴᴀᴛɪᴏɴ ᴅᴇᴄʟɪɴᴇ❌ ғᴀʟsᴇ ᴘᴀʏᴍᴇɴᴛ ᴍᴀᴅᴇ**\nContact admin for any payment-related issue.")

@Client.on_callback_query(filters.regex(r"warning_\d+") & filters.user(ADMINS))
async def warning_callback(client, callback_query):
    user_id = int(callback_query.data.split('_')[1])
    await callback_query.message.edit_text("**ᴡᴀʀɴɪɴɢ ɢɪᴠᴇɴ ᴛᴏ ᴛʜᴀᴛ ᴜsᴇʀ**")
    await client.send_message(user_id, "**❗Warning - You are violating our terms by sending explicit content. You may be banned. Contact [admin](https://t.me/Tetris_admino_bot) for more info.**")



    
