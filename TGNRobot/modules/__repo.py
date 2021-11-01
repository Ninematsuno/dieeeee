import random
from TGNRobot.events import register
from TGNRobot import telethn as fuck

sex = random.choice(['404-Not found', 'Fuck off','Please Search ur query in google.com'])

@register(pattern="^/repo (.*)")
async def sex(event):
  await fuck.send_message(event.chat_id, x, reply_to=event)