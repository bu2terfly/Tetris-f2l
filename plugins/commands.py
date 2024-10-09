import os
import logging
import random
import asyncio
from validators import domain
from Script import script
from plugins.dbusers import db
from pyrogram import Client, filters, enums
from plugins.users_api import get_user, update_user_info
from plugins.database import get_file_details
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChannelPrivate, FloodWait
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token
from config import *
import re
import json
import base64
from urllib.parse import quote_plus
from TechVJ.utils.file_properties import get_name, get_hash, get_media_file_size

logger = logging.getLogger(__name__)

BATCH_FILES = {}


FORCE_SUB_CHANNEL = -1002241072257  # Add your channel ID here


def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

async def force_sub_check(client, user_id):
    try:
        # Check if the user is a member of the update channel
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        
        # If the user is a member, administrator, or owner, return True
        if user.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
        
        # Otherwise, the user is not a member
        return False
    
    # Handle case where the user is not a participant
    except UserNotParticipant:
        return False
    
    # Handle permission or access-related issues
    except (ChatAdminRequired, ChannelPrivate) as e:
        logger.error(f"Bot lacks permission to check subscription or channel is private: {e}")
        return False
    
    # Catch any other exceptions
    except Exception as e:
        logger.error(f"Unexpected error checking subscription status: {e}")
        return False



@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    username = (await client.get_me()).username

    # Force sub check
    is_subscribed = await force_sub_check(client, message.from_user.id)
    
    if not is_subscribed:
        buttons = [[
            InlineKeyboardButton('🛸ᴜᴘᴅᴀᴛᴇ  ᴄʜᴀɴɴᴇʟ', url="https://t.me/Tetris_botz")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text="**ᴛᴏ  ᴘʀᴇᴠᴇɴᴛ  ᴏᴠᴇʀʟᴏᴀᴅ  ᴏɴʟʏ  ᴏᴜʀ  ᴄʜᴀɴɴᴇʟ  ᴜsᴇʀs  ᴄᴀɴ  ᴜsᴇ  ᴛʜɪs  ʙᴏᴛ,  ʙᴜᴛ  ᴜ ʀ  ɴᴏᴛ \n\nᴊᴏɪɴ  ᴏᴜʀ  ᴄʜᴀɴɴᴇʟ  ᴀɴᴅ  sᴇɴᴅ**  /start  **ᴀɢᴀɪɴ**",
            reply_markup=reply_markup
        )
        return


    # Check if user exists in the database
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))

    # If no extra commands provided, show start message
    
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('🪧ʜᴏᴡ  ᴛᴏ  ᴜsᴇ', callback_data='help')
            ],[
            InlineKeyboardButton('🛸ᴅᴇᴠᴇʟᴏᴘᴇʀ', url='https://t.me/tetris_botz'),
            InlineKeyboardButton('ᴡᴀʀɴɪɴɢ⚠️', callback_data='about')
            ],[
            InlineKeyboardButton('💸ᴅᴏɴᴀᴛᴇ  ᴀɴᴅ  ɢᴇᴛ  ᴘʀᴇᴍɪᴜᴍ', callback_data='pay')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        me2 = (await client.get_me()).mention
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, me2),
            reply_markup=reply_markup
        )
        return
    

    
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            await message.reply_text(
                text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all files till today midnight.</b>",
                protect_content=True
            )
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
    elif data.split("-", 1)[0] == "BATCH":
        try:
            if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
                btn = [[
                    InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
                ],[
                    InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
                ]]
                await message.reply_text(
                    text="<b>You are not verified !\nKindly verify to continue !</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
        except Exception as e:
            return await message.reply_text(f"**Error - {e}**")
        sts = await message.reply("**🔻 ᴜᴘʟᴏᴀᴅɪɴɢ....**")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
            
        filesarr = []
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                if STREAM_MODE == True:
                    # Create the inline keyboard button with callback_data
                    user_id = message.from_user.id
                    username =  message.from_user.mention 

                    log_msg = await client.send_cached_media(
                        chat_id=LOG_CHANNEL,
                        file_id=msg.get("file_id"),
                    )
                    fileName = {quote_plus(get_name(log_msg))}
                    stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
 
                    await log_msg.reply_text(
                        text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                        quote=True,
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Fast Download 🚀", url=download),  # we download Link
                                                            InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)]])  # web stream Link
                    )
                if STREAM_MODE == True:
                    button = [[
                        InlineKeyboardButton("✦ sᴛʀᴇᴀᴍ  ᴏɴʟɪɴᴇ", url=stream),  # we download Link
                        InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ  ғᴀsᴛ ✦', url=download)
                    ],[
                        InlineKeyboardButton("• ᴡᴀᴛᴄʜ  ᴏɴ  ᴛᴇʟᴇɢʀᴀᴍ  ᴡᴇʙ •", web_app=WebAppInfo(url=stream))
                    ]]
                    reply_markup=InlineKeyboardMarkup(button)
                else:
                    reply_markup = None
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=reply_markup
                )
                filesarr.append(msg)
                
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(button)
                )
                filesarr.append(msg)
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        
        k = await client.send_message(chat_id = message.from_user.id, text=f"**❗️ɴᴏᴛᴇ **:  files  are  deleted  after  10  minutes  due  to  copyright  issue.  use  the  link  for  retrieve  it  anytime")
        
        await asyncio.sleep(600)
        for x in filesarr:
           try:
               await x.delete()  # Delete file
           except Exception as e:
               logger.warning(e)
    



    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
            btn = [[
                InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
            ],[
                InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
            ]]
            await message.reply_text(
                text="<b>You are not verified !\nKindly verify to continue !</b>",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=(pre == 'filep')
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = '' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), file.file_name.split()))
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            
            await msg.edit_caption(f_caption)
            
            if STREAM_MODE:
                await msg.edit_reply_markup(
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    '✦ ɢᴇɴᴇʀᴀᴛᴇ  ғᴀsᴛ  ᴅᴏᴡɴʟᴏᴀᴅ/sᴛʀᴇᴀᴍ  ʟɪɴᴋ ✦', callback_data=f'generate_stream_link:{file_id}'
                                )
                            ]
                        ]
                    )
                )
                
            if AUTO_DELETE_MODE == True:
                k = await client.send_message(chat_id = message.from_user.id, text=f"❗️**ɴᴏᴛᴇ**: files  are  deleted  after  10  minutes  due  to  copyright  issue.  use  the  link  for  retrieve  it  anytime")
                await asyncio.sleep(20)
                try:
                    await msg.delete()
            return
        except Exception as e:
            return await message.reply('<i>ɪ  ғᴏᴜɴᴅ  ɴᴏᴛʜɪɴɢ... ᴀʀᴇ  ʏᴏᴜ  sᴜʀᴇ</i>**')


    
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
        btn = [[
            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
        ],[
            InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
        ]]
        await message.reply_text(
            text="<b>You are not verified !\nKindly verify to continue !</b>",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
    x = await client.send_cached_media(
    chat_id=message.from_user.id,
    file_id=file_id,
    caption=f_caption,  # Caption for the file
    protect_content=True if pre == 'filep' else False
    )
    
    if STREAM_MODE:
        g = await x.edit_caption(
            caption=f"{f_caption}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('✦ ɢᴇɴᴇʀᴀᴛᴇ  ғᴀsᴛ  ᴅᴏᴡɴʟᴏᴀᴅ/sᴛʀᴇᴀᴍ  ʟɪɴᴋ ✦', callback_data=f'generate_stream_link:{file_id}')
                    ]
                ]
            )
        )
    if AUTO_DELETE_MODE == True:
        k = await client.send_message(chat_id = message.from_user.id, text=f"❗️**ɴᴏᴛᴇ**: file  are  deleted  after  10  minutes  due  to  copyright  issue.  use  the  link  for  retrieve  it  anytime")
        await asyncio.sleep(AUTO_DELETE_TIME)
        try:
            await x.delete()
        except:
            pass
        await k.edit_text("<i>ғɪʟᴇ  ᴅᴇʟᴇᴛᴇᴅ  ᴜsᴇ  ʀᴇᴛʀɪᴇᴠᴇ  ʟɪɴᴋ  ᴛᴏ  ɢᴇᴛ  ᴀɢᴀɪɴ</i>")       
        

@Client.on_message(filters.command('api') & filters.private)
async def shortener_api_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command

    if len(cmd) == 1:
        s = script.SHORTENER_API_MESSAGE.format(base_site=user["base_site"], shortener_api=user["shortener_api"])
        return await m.reply(s)

    elif len(cmd) == 2:    
        api = cmd[1].strip()
        await update_user_info(user_id, {"shortener_api": api})
        await m.reply("**sʜᴏʀᴛɴᴇʀ  ᴀᴘɪ  ᴀᴅᴅᴇᴅ  ʜᴇʀᴇs  ɪᴛ  ɪs - **" + api)


@Client.on_message(filters.command("shortner") & filters.private)
async def base_site_handler(client, m: Message):
    user_id = m.from_user.id
    
    if user_id not in P_USERS:
        return await m.reply("**❌ ʏᴏᴜ  ᴅᴏɴᴛ  ʜᴀᴠᴇ  ᴘʀᴇᴍɪᴜᴍ  ᴄᴏᴍᴍᴀɴᴅ  ᴀᴄᴄᴇss** \n\n/shortner  command  use  for  adding  your  own  shortner  then  bot  will  convert  file  retrieve  link  to  shorten  link")
            
    user = await get_user(user_id)
    cmd = m.command
    text = f"**ɪɴᴠᴀʟɪᴅ  ғᴏʀᴍᴀᴛ  sᴇɴᴅ  ʟɪᴋᴇ  ᴛʜɪs** : \n\n**/shortner (shortnerdomain)\nᴇxᴍᴘʟᴇ** - `/shortner shrinkme.link `\n\nTo  remove  shortner  send  this👉🏻 `/shortner none`"
    
    # If no argument is provided, show instructions
    if len(cmd) == 1:
        return await m.reply(text=text, disable_web_page_preview=True)
    
    # If the argument is provided
    elif len(cmd) == 2:
        base_site = cmd[1].strip()
        
        # If the user wants to remove the base site
        if base_site.lower() == "none":
            await update_user_info(user_id, {"base_site": None})  # Set base_site to None
            return await m.reply("<b>sʜᴏʀᴛɴᴇʀ  ʀᴇᴍᴏᴠᴇᴅ..... ᴄʜᴇᴄᴋ  ʜᴇʀᴇ 👉🏻  /api</b>")
        
        # Check if the provided base site is a valid domain
        if not domain(base_site):
            return await m.reply(text=text, disable_web_page_preview=True)
        
        # Update the base site with the provided value
        await update_user_info(user_id, {"base_site": base_site})
        await m.reply("<b>sʜᴏʀᴛɴᴇʀ  ᴜᴘᴅᴀᴛᴇᴅ...... ᴄʜᴇᴄᴋ  ʜᴇʀᴇ 👉🏻 /api</b>")


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('◀️ʙᴀᴄᴋ', callback_data='start')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        me2 = (await client.get_me()).mention
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(me2),
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )


    
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('🪧ʜᴏᴡ  ᴛᴏ  ᴜsᴇ', callback_data='help')
            ],[
            InlineKeyboardButton('🛸ᴅᴇᴠᴇʟᴏᴘᴇʀ', url='https://t.me/tetris_botz'),
            InlineKeyboardButton('ᴡᴀʀɴɪɴɢ⚠️', callback_data='about')
            ],[
            InlineKeyboardButton('💸ᴅᴏɴᴀᴛᴇ  ᴀɴᴅ  ɢᴇᴛ  ᴘʀᴇᴍɪᴜᴍ', callback_data='pay')
        ]]
    
        reply_markup = InlineKeyboardMarkup(buttons)
    
    # No image media, using edit_text with web page preview enabled
        me2 = (await client.get_me()).mention
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, me2),
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
    
    elif query.data == "pay":
        buttons = [[
            InlineKeyboardButton('💸ᴄʟɪᴄᴋ  ʜᴇʀᴇ  ᴛᴏ  ᴅᴏɴᴀᴛᴇ', callback_data='payment')
        ],[
            InlineKeyboardButton('◀️ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('ᴀᴅᴍɪɴ🛸', url='https://t.me/tetris_admino_bot')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CLONE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )          

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
    
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('◀️ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('ᴀᴅᴍɪɴ🛸', url='https://t.me/Tetris_admino_bot')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )

    elif query.data == "payment":
        new_image_path = "https://telegra.ph/file/4a0a3ac73658ff4c68dff.jpg"
        await query.message.edit_media(
            media=InputMediaPhoto(new_image_path, caption=script.PAYMENT),
            reply_markup=InlineKeyboardMarkup([[
             InlineKeyboardButton("ᴀᴍᴏᴜɴᴛ ᴘᴀɪᴅ ✅", callback_data = "paid")]])) 
    
    
    elif query.data == "paid":
        user_id = query.from_user.id
        user_mention = query.from_user.mention
        
        log_message = (
            f"🇷 🇪 🇲 🇮 🇳 🇩 🇪 🇷 🇸 \n\n"
            f"**ᴜsᴇʀɴᴀᴍᴇ** - {user_mention}\n"
            f"**ɪᴅ**: <code>{user_id}</code>\n"
            f"**ᴀᴄᴛɪᴏɴ** - ᴅᴏɴᴀᴛᴇ\n"
            f"**ᴛɪᴍᴇ** - ᴄʜᴇᴄᴋ ʜᴇʀᴇ👉🏻"
        )

        

        # Sending log message to the admin log channel
        await client.send_message(LOG_CHANNEL, text=log_message)

        # Step 2: Respond to the user with transaction details
        await query.message.edit_text(
            text=(
                "**🥳ᴅᴇᴇᴘʟʏ  ɢʀᴀᴛᴇғᴜʟʟ  ᴛᴏ  ʏᴏᴜʀ  ᴅᴏɴᴀᴛɪᴏɴ💸 \nᴡᴀɪᴛ  ᴀᴅᴍɪɴ  ᴡɪʟʟ  ᴠᴇʀɪғʏ  ʏᴏᴜ  sʜᴏʀᴛʟʏ\n\nsᴛᴀᴛᴜs - ᴛʀᴀɴsᴀᴄᴛɪᴏɴ  ᴘʀᴏᴄᴇssɪɴɢ🔄**\n"
                f"**ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ɪᴅ:** `FLC28<code>{user_id}</code>P`\n\n"
                "**ɴᴏᴛᴇ -** send you channel link or any other content to admin for showcasing. also mention your transaction ID "
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛸ᴀᴅᴍɪɴ", url="https://t.me/tetris_admino_bot")]
            ])
        )



       

    elif query.data.startswith("generate_stream_link"):
        _, file_id = query.data.split(":")
        try:
            user_id = query.from_user.id
            username =  query.from_user.mention 

            log_msg = await client.send_cached_media(
                chat_id=LOG_CHANNEL,
                file_id=file_id,
            )
            fileName = {quote_plus(get_name(log_msg))}
            stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
            download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

            xo = await query.message.reply_text(f'⌨️')
            await asyncio.sleep(1)
            await xo.delete()

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

            button = [[
                InlineKeyboardButton("🚀 Fast Download 🚀", url=download),  # we download Link
                InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)
            ]]
            reply_markup=InlineKeyboardMarkup(button)
            await log_msg.reply_text(
                text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            button = [[
                InlineKeyboardButton("⟡ sᴛʀᴇᴀᴍ  ᴏɴʟɪɴᴇ", url=download),  # we download Link
                InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ  ғᴀsᴛ ⟡', url=stream)
            ],[
                InlineKeyboardButton("• ᴡᴀᴛᴄʜ  ᴏɴ  ᴛᴇʟᴇɢʀᴀᴍ  ᴡᴇʙ •", web_app=WebAppInfo(url=stream))
            ]]
            reply_markup=InlineKeyboardMarkup(button)
            await query.message.reply_text(
                text="**ʟɪɴᴋ  ɢᴇɴᴇʀᴀᴛᴇᴅ , ᴄʟɪᴄᴋ  ʙᴇʟᴏᴡ [🔽](https://telegra.ph/file/6b18b34bad2f27c96afe8.mp4) ʙᴜᴛᴛᴏɴs**\n\nlong  press  any  buttons  to  copy  links  and  share",
                quote=True,
                disable_web_page_preview=False,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(e)  # print the error message
            await query.answer(f"something went wrong\n\n{e}", show_alert=True)
            return

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
