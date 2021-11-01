from TGNRobot import pbot as app
from TGNRobot.utils.dbfunctions import (update_karma, get_karma, get_karmas,
                                   int_to_alpha, alpha_to_int, is_karma_on,
                                   karma_on, karma_off)

from TGNRobot.utils.filter_groups import karma_positive_group, karma_negative_group
from pyrogram import filters

__MODULE__ = "Karma"
__HELP__ = """[UPVOTE] - Use upvote keywords like "+", "+1", "thanks" etc to upvote a message.
[DOWNVOTE] - Use downvote keywords like "-", "-1", etc to downvote a message.
Reply to a message with /karma to check a user's karma
Send /karma without replying to any message to chek karma list of top 10 users"""

async def member_permissions(chat_id, user_id):
    perms = []
    member = (await app.get_chat_member(chat_id, user_id))
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_voice_chats:
        perms.append("can_manage_voice_chats")
    return perms


regex_upvote = r"^((?i)\+|\+\+|\+1|thx|tnx|ty|thank you|thanx|thanks|pro|cool|good|👍)$"
regex_downvote = r"^(\-|\-\-|\-1|👎)$"


@app.on_message(
    filters.text
    & filters.group
    & filters.incoming
    & filters.reply
    & filters.regex(regex_upvote)
    & ~filters.via_bot
    & ~filters.bot
    & ~filters.edited,
    group=karma_positive_group
)
async def upvote(_, message):
    if not await is_karma_on(message.chat.id):
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        return
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id
    user_mention = message.reply_to_message.from_user.mention
    current_karma = await get_karma(chat_id, await int_to_alpha(user_id))
    if current_karma:
        current_karma = current_karma['karma']
        karma = current_karma + 1
        new_karma = {"karma": karma}
        await update_karma(chat_id, await int_to_alpha(user_id), new_karma)
    else:
        karma = 1
        new_karma = {"karma": karma}
        await update_karma(chat_id, await int_to_alpha(user_id), new_karma)
    await message.reply_text(
        f'Incremented Karma of {user_mention} By 1 \nTotal Points: {karma}'
    )


@app.on_message(
    filters.text
    & filters.group
    & filters.incoming
    & filters.reply
    & filters.regex(regex_downvote)
    & ~filters.via_bot
    & ~filters.bot
    & ~filters.edited,
    group=karma_negative_group
)
async def downvote(_, message):
    if not await is_karma_on(message.chat.id):
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        return
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id
    user_mention = message.reply_to_message.from_user.mention
    current_karma = await get_karma(chat_id, await int_to_alpha(user_id))
    if current_karma:
        current_karma = current_karma['karma']
        karma = current_karma - 1
        new_karma = {"karma": karma}
        await update_karma(chat_id, await int_to_alpha(user_id), new_karma)
    else:
        karma = 1
        new_karma = {"karma": karma}
        await update_karma(chat_id, await int_to_alpha(user_id), new_karma)
    await message.reply_text(
        f'Decremented Karma Of {user_mention} By 1 \nTotal Points: {karma}'
    )


@app.on_message(filters.command("karma") & filters.group)
async def karma(_, message):
    chat_id = message.chat.id

    if not message.reply_to_message:
        karma = await get_karmas(chat_id)
        msg = f"**Karma list of {message.chat.title}:- **\n"
        limit = 0
        karma_dicc = {}
        for i in karma:
            user_id = await alpha_to_int(i)
            user_karma = karma[i]['karma']
            karma_dicc[str(user_id)] = user_karma
            karma_arranged = dict(
                sorted(karma_dicc.items(), key=lambda item: item[1], reverse=True))
        for user_idd, karma_count in karma_arranged.items():
            if limit > 9:
                break
            try:
                user_name = (await app.get_users(int(user_idd))).username
            except Exception:
                continue
            msg += f"{user_name} : `{karma_count}`\n"
            limit += 1
        await message.reply_text(msg)
    else:
        user_id = message.reply_to_message.from_user.id
        karma = await get_karma(chat_id, await int_to_alpha(user_id))
        if karma:
            karma = karma['karma']
            await message.reply_text(f'**Total Points**: __{karma}__')
        else:
            karma = 0
            await message.reply_text(f'**Total Points**: __{karma}__')


@app.on_message(filters.command("karmastat") & ~filters.private)
async def captcha_state(_, message):
    usage = "**Usage:** karmastat ON or OFF "
    if len(message.command) != 2:
        await message.reply_text(usage)
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    permissions = await member_permissions(chat_id, user_id)
    if "can_restrict_members" not in permissions:
        await message.reply_text("You don't have enough permissions.")
        return
    state = message.text.split(None, 1)[1].strip()
    state = state.lower()
    if state == "on":
        await karma_on(chat_id)
        await message.reply_text("Enabled karma system.")
    elif state == "off":
        await karma_off(chat_id)
        await message.reply_text("Disabled karma system.")
    else:
        await message.reply_text(usage)
