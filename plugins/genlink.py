# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import requests
from pyrogram import filters, Client, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE, P_USERS
from plugins.database import unpack_new_file_id
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from plugins.users_api import get_user, get_short_link
import re
import os
import json
import base64
import logging

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)




async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

def upload_image_requests(image_path):
    """Upload image to the server."""
    upload_url = "https://envs.sh"  # Make sure this URL is correct and functional
    try:
        with open(image_path, 'rb') as file:
            files = {'file': file}
            # Adding timeout for the request (e.g., 30 seconds)
            response = requests.post(upload_url, files=files, timeout=30)
            
            # Logging the response status and content
            logger.info(f"Upload response status: {response.status_code}")
            logger.debug(f"Upload response content: {response.text}")

            if response.status_code == 200:
                return response.text.strip()  # Ensure this returns the actual URL
            else:
                raise Exception(f"Upload failed with status code {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error("Upload timed out.")
        return None
    except Exception as e:
        logger.error(f"Error during upload: {e}")
        return None


# Handle Photo uploads
@Client.on_message(filters.private & filters.photo)
async def handle_photo(bot, message):
    try:
        # Download the photo to the local system
        photo_path = await message.download()
        if not photo_path:
            raise Exception("Failed to download photo.")

        # Inform the user that the upload process is starting
        uploading_message = await message.reply_text("ᴜᴘʟᴏᴀᴅɪɴɢ  ɪᴍᴀɢᴇ....")

        # Upload the photo to the external server
        photo_url = upload_image_requests(photo_path)

        # If the upload fails, raise an error
        if not photo_url:
            raise Exception("ғᴀɪʟᴇᴅ  ᴛᴏ  ᴜᴘʟᴏᴀᴅ....  ᴄᴏɴᴛᴀᴄᴛ  ᴀᴅᴍɪɴ")

        # Edit the message to show the hosted photo URL and options
        await uploading_message.edit_text(
            text=f"**🌄ᴘʜᴏᴛᴏ  ʜᴏsᴛᴇᴅ  ᴏɴ  ᴇɴᴠs.sʜ  ʟɪɴᴋs  ʜᴇʀᴇ:**\n\n"
                 f"ᴛᴀᴘ  ʟɪɴᴋ  ᴛᴏ  ᴄᴏᴘʏ: <code>{photo_url}</code>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text="ᴏᴘᴇɴ  ʟɪɴᴋ", url=photo_url),
                InlineKeyboardButton(text="sʜᴀʀᴇ  ʟɪɴᴋ", url=f"https://telegram.me/share/url?url={photo_url}")
            ]])
        )

        # Clean up: remove the downloaded photo file from local storage
        os.remove(photo_path)

    except Exception as e:
        # Log the error details for debugging
        logger.error(f"Error handling photo: {e}")
        await message.reply_text(f"An error occurred while processing the photo: {e}")



        
# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

@Client.on_message(filters.private & filters.create(allowed) & (filters.document | filters.video | filters.audio))
async def handle_media(bot, message):
    try:
        username = (await bot.get_me()).username
        file_type = message.media
        file_id, ref = unpack_new_file_id((getattr(message, file_type.value)).file_id)
        string = 'file_'
        string += file_id
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        user_id = message.from_user.id
        user = await get_user(user_id)

        # Generate the file link
        if WEBSITE_URL_MODE:
            share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
        else:
            share_link = f"https://t.me/{username}?start={outstr}"

        if user["base_site"] and user["shortener_api"]:
            short_link = await get_short_link(user, share_link)
            button_text = "ʜᴇʀᴇ's ᴛʜᴇ sʜᴏʀᴛ ʟɪɴᴋ"
            button_link = short_link
        else:
            button_text = "ʀᴇᴛʀɪᴇᴠᴇ ᴏʀ ɢᴇᴛ ғɪʟᴇ"
            button_link = share_link

        # Reply with the link
        reply_text = (
            "**⭕ ғɪʟᴇ sᴛᴏʀᴇᴅ ғᴏʀ ʀᴇᴛʀɪᴇᴠɪɴɢ, ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ**\n\n
            "long press buttons to copy the link and share"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text, url=button_link)]
        ])

        await message.reply(reply_text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error handling media: {e}")
        await message.reply_text(f"An error occurred while processing the media: {e}")
        



@Client.on_message(filters.command(['batch', 'pbatch']) & filters.private)
async def gen_link_batch(bot, message):
    user_id = message.from_user.id
    
    # Check if the user is in the approved users list
    if user_id not in P_USERS:
        return await message.reply("**❌ ʏᴏᴜ  ᴅᴏɴᴛ  ʜᴀᴠᴇ  ᴘʀᴇᴍɪᴜᴍ  ᴄᴏᴍᴍᴀɴᴅ  ᴀᴄᴄᴇss** \n\n /batch  command  use  for  generating  download / stream  link  for  multiple  files  direct  from  your  channel  at  once")
    
    username = (await bot.get_me()).username
    if " " not in message.text:
        return await message.reply("ɪɴᴠᴀʟɪᴅ/ᴡʀᴏɴɢ  ғᴏʀᴍᴀᴛ  sᴇɴᴅ  ʟɪᴋᴇ  ᴛʜɪs** \n /batch [channel post link1] [channel post link2] \n\n**ᴇx** - /batch https://t.me/demo/123 https://t.me/demo/456")
    
    links = message.text.strip().split(" ")
    if len(links) != 3:
        return await message.reply("ɪɴᴠᴀʟɪᴅ/ᴡʀᴏɴɢ  ғᴏʀᴍᴀᴛ  sᴇɴᴅ  ʟɪᴋᴇ  ᴛʜɪs** \n /batch [channel post link1] [channel post link2] \n\n**ᴇx** - /batch https://t.me/demo/123 https://t.me/demo/456")
    
    cmd, first, last = links
    regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
    
    match = regex.match(first)
    if not match:
        return await message.reply('**ʟᴏᴏᴋs  ʟɪᴋᴇ  ʟɪɴᴋs  ᴀʀᴇ  ɪɴᴠᴀʟɪᴅ**')
    
    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    if f_chat_id.isnumeric():
        f_chat_id = int(("-100" + f_chat_id))
    
    match = regex.match(last)
    if not match:
        return await message.reply('**ʟᴏᴏᴋs  ʟɪᴋᴇ  ʟɪɴᴋs  ᴀʀᴇ  ɪɴᴠᴀʟɪᴅ**')
    
    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))
    if l_chat_id.isnumeric():
        l_chat_id = int(("-100" + l_chat_id))
    
    if f_chat_id != l_chat_id:
        return await message.reply("ᴄʜᴀɴɴᴇʟ  ɪᴅ  ɴᴏᴛ  ᴍᴀᴛᴄʜᴇᴅ")
    
    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply('ᴍᴀᴋᴇ  ᴍᴇ  ᴀᴅᴍɪɴ  ɪɴ  ᴛʜᴀᴛ  ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('**ʟᴏᴏᴋs  ʟɪᴋᴇ  ɪɴᴠᴀʟɪᴅ  ʟɪɴᴋs  sᴘᴇᴄɪғɪᴇᴅ**')
    except Exception as e:
        return await message.reply(f'ᴇʀʀᴏʀ - {e}')
    
    sts = await message.reply("**ɪɴᴅᴇxɪɴɢ  ғɪʟᴇ  ғʀᴏᴍ  ᴄʜᴀɴɴᴇʟ.... ᴘʟᴇᴀsᴇ  ᴡᴀɪᴛ** \n\nwaiting  time  depends  on  number  of  files  for  indexing")

    FRMT = "**ɢᴇɴᴇʀᴀᴛɪɴɢ ʟɪɴᴋ...**\n**ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs:** {total}\n**ᴅᴏɴᴇ:** {current}\n**ʀᴇᴍᴀɪɴɪɴɢ:** {rem}\n**sᴛᴀᴛᴜs:** {sts}"

    outlist = []
    og_msg = 0
    tot = 0
    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        tot += 1
        if msg.empty or msg.service:
            continue
        if not msg.media:
            # only media messages supported.
            continue
        try:
            file_type = msg.media
            file = getattr(msg, file_type.value)
            caption = getattr(msg, 'caption', '')
            if caption:
                caption = caption.html
            if file:
                file = {
                    "file_id": file.file_id,
                    "caption": caption,
                    "title": getattr(file, "file_name", ""),
                    "size": file.file_size,
                    "protect": cmd.lower().strip() == "/pbatch",
                }
                og_msg += 1
                outlist.append(file)
        except:
            pass
        if not og_msg % 20:
            try:
                await sts.edit(FRMT.format(total=l_msg_id-f_msg_id, current=tot, rem=((l_msg_id-f_msg_id) - tot), sts="Saving Messages"))
            except:
                pass

    with open(f"batchmode_{message.from_user.id}.json", "w+") as out:
        json.dump(outlist, out)
    
    post = await bot.send_document(LOG_CHANNEL, f"batchmode_{message.from_user.id}.json", file_name="Batch.json", caption="⚠️Generated for filestore.")
    os.remove(f"batchmode_{message.from_user.id}.json")
    file_id, ref = unpack_new_file_id(post.document.file_id)
    
    user = await get_user(user_id)
    if WEBSITE_URL_MODE:
        share_link = f"{WEBSITE_URL}?Tech_VJ=BATCH-{file_id}"
    else:
        share_link = f"https://t.me/{username}?start=BATCH-{file_id}"
    
    if user["base_site"] and user["shortener_api"] != None:
        short_link = await get_short_link(user, share_link)
        await sts.edit(f"<b>⭕ ғɪʟᴇs  sᴛᴏʀᴇᴅ  ʜᴇʀᴇ  ɪs  ʏᴏᴜʀ  ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛᴇɴ  ʟɪɴᴋ :- {short_link}</b>")
    else:
        await sts.edit(f"<b>⭕ ғɪʟᴇs  sᴛᴏʀᴇᴅ  ʜᴇʀᴇ  ɪs  ʏᴏᴜʀ  ʟɪɴᴋ:\n\n🔗 ʀᴇᴛʀɪᴇᴠᴇ  ʟɪɴᴋ :- {share_link}</b>")
        
