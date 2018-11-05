import json
import os
import sys

from discord import TextChannel
from discord.ext import commands

if not os.path.isfile('config.json'):
    if not os.path.isfile('config.json.example'):
        print("config.json could not be found! Please get the example copy from GitHub and rename it to config.json!")
        sys.exit(1)
    else:
        print("config.json could not be found! (Did you rename config.json.example to config.json yet?)")
        sys.exit(1)

with open("config.json", "r+") as j:
    data = json.load(j)
token = data.get('token', None)
prefix = data.get('prefix', "%")
if token is None:
    print("No bot token was specified!")
    sys.exit(1)

bot = commands.Bot(command_prefix=prefix)
is_search_running = False


@bot.event
async def on_ready():
    print("I'm ready!")


@bot.event
async def on_command_error(ctx, error):
    global is_search_running, is_index_running
    if ctx.command.name == "tfp":
        is_search_running = False


@bot.event
async def on_message(msg):
    ctx = await bot.get_context(msg)
    if ctx.invoked_with:
        await bot.invoke(ctx)


@bot.command()
async def tfp(ctx, *, phrase: str):
    global is_search_running
    if is_search_running:
        await ctx.send("Already running a search, wait your turn.")
        return
    is_search_running = True
    await ctx.send("Searching for occurrences of `{}`...".format(phrase))
    async with ctx.typing():
        totals = dict()
        for channel in (c for c in ctx.guild.channels if type(c) is TextChannel and c.permissions_for(ctx.guild.me).read_message_history):
            msgs = await channel.history(limit=None, before=ctx.message).flatten()
            for msg in msgs:
                ct = msg.content.lower().count(phrase.lower())
                if ct > 0:
                    if msg.author.name not in totals:
                        totals[msg.author.name] = ct
                    else:
                        totals[msg.author.name] += ct

        if len(totals) == 0:
            await ctx.send("No one has ever said that.")
            is_search_running = False
            return

        maxw_name = len(max(totals, key=len))
        grand_total = sum(totals.values())
        maxw_tots = len(str(grand_total))

        out = "Total usages of the phrase `{0}`: **{1}**\nTop posters:\n```".format(phrase, grand_total)
        for i, user in enumerate(sorted(totals, key=totals.get, reverse=True), start=1):
            if i > 10:
                break
            out += "\n{0:<2}. {1:<{mn}}  {2:{mt}} uses | {3:5.01f}%".format(i, user.ljust(maxw_name), str(totals[user]).rjust(maxw_tots), float(totals[user]) / grand_total * 100, mn=maxw_name, mt=maxw_tots)
        out += "```"
        await ctx.send(out)
        is_search_running = False

bot.run(token)
