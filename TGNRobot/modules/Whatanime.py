import random
import requests
import os
import asyncio
import shlex
import tracemoepy
from os.path import basename
from uuid import uuid4
from tracemoepy.errors import ServerError
from aiohttp import ClientSession
from typing import Tuple, Optional
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)


from TGNRobot import pbot

TRACE_MOE = {}
DOWN_PATH = "./TGNRobot/"

ISADULT = """
query ($id: Int) {
  Media (id: $id) {
    isAdult
  }
}
"""


def rand_key():
    return str(uuid4())[:8]


async def runcmd(cmd: str) -> Tuple[str, str, int, int]:
    """run command in terminal"""
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


async def return_json_senpai(
    query: str, vars_: dict, auth: bool = False, user: int = None
):
    if auth is False:
        url = "https://graphql.anilist.co"
        response = requests.post(url, json={"query": query, "variables": vars_}).json()
    return response


async def check_if_adult(id_):
    vars_ = {"id": int(id_)}
    k = await return_json_senpai(query=ISADULT, vars_=vars_, auth=False)
    if str(k["data"]["Media"]["isAdult"]) == "True":
        return "False"
    else:
        return "False"


async def take_screen_shot(
    video_file: str, duration: int, path: str = ""
) -> Optional[str]:
    """take a screenshot"""
    print(
        "[[[Extracting a frame from %s ||| Video duration => %s]]]",
        video_file,
        duration,
    )
    ttl = duration // 2
    thumb_image_path = path or os.path.join(DOWN_PATH, f"{basename(video_file)}.jpg")
    command = f'''ffmpeg -ss {ttl} -i "{video_file}" -vframes 1 "{thumb_image_path}"'''
    err = (await runcmd(command))[1]
    if err:
        print(err)
    return thumb_image_path if os.path.exists(thumb_image_path) else None


async def media_to_image(
    client: Client, message: Message, x: Message, replied: Message
):
    if not (replied.photo or replied.sticker or replied.animation or replied.video):
        await x.edit_text("Media Type Is Invalid !")
        await asyncio.sleep(5)
        await x.delete()
        return
    media = replied.photo or replied.sticker or replied.animation or replied.video
    if not os.path.isdir(DOWN_PATH):
        os.makedirs(DOWN_PATH)
    dls = await client.download_media(
        media,
        file_name=DOWN_PATH + rand_key(),
    )
    dls_loc = os.path.join(DOWN_PATH, os.path.basename(dls))
    if replied.sticker and replied.sticker.file_name.endswith(".tgs"):
        png_file = os.path.join(DOWN_PATH, f"{rand_key()}.png")
        cmd = f"lottie_convert.py --frame 0 -if lottie -of png {dls_loc} {png_file}"
        stdout, stderr = (await runcmd(cmd))[:2]
        os.remove(dls_loc)
        if not os.path.lexists(png_file):
            await x.edit_text("This sticker is invalid, Task Failed Successfully")
            await asyncio.sleep(5)
            await x.delete()
            raise Exception(stdout + stderr)
        dls_loc = png_file
    elif replied.sticker and replied.sticker.file_name.endswith(".webp"):
        stkr_file = os.path.join(DOWN_PATH, f"{rand_key()}.png")
        os.rename(dls_loc, stkr_file)
        if not os.path.lexists(stkr_file):
            await x.edit_text("```Sticker not found...```")
            await asyncio.sleep(5)
            await x.delete()
            return
        dls_loc = stkr_file
    elif replied.animation or replied.video:
        await x.edit_text("`Converting Media To Image ...`")
        jpg_file = os.path.join(DOWN_PATH, f"{rand_key()}.jpg")
        await take_screen_shot(dls_loc, 0, jpg_file)
        os.remove(dls_loc)
        if not os.path.lexists(jpg_file):
            await x.edit_text("This Gif is invalid (╥﹏╥), Task Failed Successfully")
            await asyncio.sleep(5)
            await x.delete()
            return
        dls_loc = jpg_file
    return dls_loc


no_pic = [
    "https://telegra.ph/file/0d2097f442e816ba3f946.jpg",
    "https://telegra.ph/file/5a152016056308ef63226.jpg",
    "https://telegra.ph/file/d2bf913b18688c59828e9.jpg",
    "https://telegra.ph/file/d53083ea69e84e3b54735.jpg",
    "https://telegra.ph/file/b5eb1e3606b7d2f1b491f.jpg",
]

# suzuya beta bot

@pbot.on_message(filters.command("whatanime"))
async def whatanime(client: Client, message: Message):
    gid = message.chat.id
    x = await message.reply_text("Reverse searching the given media")
    replied = message.reply_to_message
    if not replied:
        await x.edit_text("Reply to some media !")
        await asyncio.sleep(5)
        await x.delete()
        return
    dls_loc = await media_to_image(client, message, x, replied)
    if dls_loc:
        async with ClientSession() as session:
            tracemoe = tracemoepy.AsyncTrace(session=session)
            try:
                search = await tracemoe.search(dls_loc, upload_file=True)
            except ServerError:
                await x.edit_text("ServerError, retrying")
                try:
                    search = await tracemoe.search(dls_loc, upload_file=True)
                except ServerError:
                    await x.edit_text("Couldnt parse results!!!")
                    return
            result = search["result"][0]
            caption_ = (
                f"**Title**: {result['anilist']['title']['english']} (`{result['anilist']['title']['native']}`)\n"
                f"\n**Anilist ID:** `{result['anilist']['id']}`"
                f"\n**Similarity**: `{(str(result['similarity']*100))[:5]}`"
                f"\n**Episode**: `{result['episode']}`"
            )
            preview = result["video"]
        nsfw = False
        button = []
        if await check_if_adult(int(result["anilist"]["id"])) == "True":
            msg = no_pic[random.randint(0, 4)]
            caption = "The results parsed seems to be 18+ and it's not allowed."
            nsfw = True
        else:
            msg = preview
            caption=caption_
            button.append(
                [
                    InlineKeyboardButton(
                        "More Info",
                        url=f"https://anilist.co/anime/{result['anilist']['id']}",
                    )
                ]
            )
        dls_js = rand_key()
        TRACE_MOE[dls_js] = dls_loc
        await (message.reply_video if nsfw is False else message.reply_photo)(
            msg, caption=caption, reply_markup=InlineKeyboardMarkup(button)
        )
    else:
        await message.reply_text("Couldn't parse results!!!")
    await x.delete()
