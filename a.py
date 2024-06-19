import discord
import os
from discord.ext import commands, tasks
from discord.ext.commands import Bot, has_permissions
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image
import io

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = Bot(command_prefix='!', intents=intents)

# Data structures to hold warning and ban information
warns = defaultdict(int)
ban_timers = {}
timeout_timers = {}

# Helper functions
async def send_dm(user, message):
    try:
        await user.send(message)
    except discord.Forbidden:
        pass

def get_time_from_string(time_str):
    units = {'y': 'years', 'm': 'months', 'w': 'weeks', 'd': 'days'}
    unit = time_str[-1]
    if unit in units:
        value = int(time_str[:-1])
        return timedelta(**{units[unit]: value})
    return None

@bot.command()
@has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    warns[member.id] += 1
    await send_dm(member, f"You have been warned in MT League for {reason}. You have {warns[member.id]}/3 warns.")
    if warns[member.id] >= 3:
        warns[member.id] = 0
        await temp_ban(ctx, member, '10d', reason="Reached 3 warnings")

async def temp_ban(ctx, member, time_str, *, reason=None):
    duration = get_time_from_string(time_str)
    if duration:
        ban_until = datetime.now() + duration
        ban_timers[member.id] = ban_until
        await member.ban(reason=reason)
        await send_dm(member, f"You have been banned in MT League for {reason}. (10 day ban)")
        await ctx.send(f"{member} has been banned for {time_str} due to {reason}.")
        await asyncio.sleep(duration.total_seconds())
        await member.unban(reason="Temporary ban expired")
        del ban_timers[member.id]
    else:
        await ctx.send("Invalid time format.")

@bot.command()
@has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, time_str=None, *, reason=None):
    if time_str:
        await temp_ban(ctx, member, time_str, reason=reason)
    else:
        await member.ban(reason=reason)
        await send_dm(member, f"You have been permanently banned in MT League for {reason}.")
        await ctx.send(f"{member} has been permanently banned due to {reason}.")

@bot.command()
@has_permissions(administrator=True)
async def timeout(ctx, member: discord.Member, time_str, *, reason=None):
    duration = get_time_from_string(time_str)
    if duration:
        timeout_until = datetime.now() + duration
        timeout_timers[member.id] = timeout_until
        await member.timeout(until=timeout_until, reason=reason)
        await send_dm(member, f"You have been timed out in MT League for {reason}. (Timeout duration: {time_str})")
        await ctx.send(f"{member} has been timed out for {time_str} due to {reason}.")
        await asyncio.sleep(duration.total_seconds())
        await member.remove_timeout(reason="Timeout expired")
        del timeout_timers[member.id]
    else:
        await ctx.send("Invalid time format.")

@bot.command()
@has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await send_dm(member, f"You have been kicked from MT League for {reason}.")
    await ctx.send(f"{member} has been kicked due to {reason}.")

@bot.command()
async def overlay(ctx):
    if not ctx.message.attachments:
        await ctx.send('Please attach an image to overlay.')
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith(('png', 'jpg', 'jpeg')):
        await ctx.send('Please attach a valid image file (PNG, JPG, JPEG).')
        return

    overlay_img = Image.open('overlay.png').convert("RGBA")
    data = io.BytesIO(await attachment.read())
    user_img = Image.open(data).convert("RGBA")

    # Get dimensions of images
    user_width, user_height = user_img.size

    # Calculate new overlay dimensions to fit within user image while maintaining aspect ratio
    aspect_ratio = overlay_img.width / overlay_img.height
    if user_width / user_height < aspect_ratio:
        new_overlay_width = user_width
        new_overlay_height = int(user_width / aspect_ratio)
    else:
        new_overlay_height = user_height
        new_overlay_width = int(user_height * aspect_ratio)

    # Resize overlay
    overlay_img = overlay_img.resize((new_overlay_width, new_overlay_height), Image.LANCZOS)

    # Center overlay on the user image
    overlay_position = (
        (user_width - new_overlay_width) // 2,
        (user_height - new_overlay_height) // 2
    )

    user_img.paste(overlay_img, overlay_position, overlay_img)
    output = io.BytesIO()
    user_img.save(output, format='PNG')
    output.seek(0)
    await ctx.send(file=discord.File(output, 'overlayed_image.png'))

@bot.command()
async def LEAK(ctx):
    await ctx.send('<@&1230629514468392960>')

@bot.command()
async def EVENT(ctx):
    await ctx.send('<@&1242872145277747281>')

@bot.command()
async def YT(ctx):
    await ctx.send('<@&1230629339641413652>')

@bot.command()
async def POLL(ctx):
    await ctx.send('<@&1237314912829571155>')

@bot.command()
async def ANNOUNCEMENT(ctx):
    await ctx.send('<@&1230629239896801310>')

@bot.command()
async def GIVEAWAY(ctx):
    await ctx.send('<@&1230629427981979851>')

@bot.command()
async def Ping(ctx):
    await ctx.send('Pong!')

@tasks.loop(hours=24)
async def monitor_pings():
    # Implement the monitoring of pings for user <@693756059340505189>
    pass

@bot.event
async def on_ready():
    monitor_pings.start()
    print(f'Logged in as {bot.user}!')

bot.run(os.environ.get('DISCORD_BOT_TOKEN'))
