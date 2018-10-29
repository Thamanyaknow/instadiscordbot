import discord
from discord.ext import commands
import random
import json
from InstagramAPII import InstagramAPI
import time
import threading
import asyncio
import os

STOP_ACCEPT = False

description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='-', description=description)

def try_login(username, password):
    api = InstagramAPI(username, password)
    if api.login():
        return api
    else:
        print("Login Failed.")
        return False

def approve(API, userId):
    data = json.dumps({
        '_uuid': API.uuid,
        '_uid': API.username_id,
        'user_id': userId,
        '_csrftoken': API.token
    })

    return API.AcceptRequest('friendships/approve/'+ str(userId) + '/', API.generateSignature(data))

def getFollowRequests(API):
    return API.SendRequest('friendships/pending?')

def prettify(data):
    print(json.dumps(data, indent=4))

def getUserIds(data : dict):
    IDs = []
    users = data["users"]
    for user in users:
        IDs.append(user["pk"])

    return IDs

def accepter(API, userIDs):
    for userID in userIDs:
        approve(API, userID)

def split_it(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

def accept(api, threads : int):
    getFollowRequests(api)
    vv_data = api.LastJson
    userIDs = getUserIds(vv_data)

    length_ids = len(userIDs)

    splitted_ids = list(split_it(userIDs, threads))

    print("Volgverzoeken: {}".format(length_ids))

    api.update_headers_for_vv()

    t0 = time.time()

    threads_list = []

    if length_ids > 10:
        for i in range(threads):
            t = threading.Thread(target=accepter, args=(api, splitted_ids[i]))
            threads_list.append(t)
            t.daemon = True
            t.start()
        for x in threads_list:
            x.join()
    else:
        accepter(api, userIDs)

    t1 = time.time()
    time_difference = t1 - t0
    time_seconds = round(time_difference, 2)
    time_minutes = round(time_difference / 60, 2)

    print("Took {} Seconds | {} Minutes".format(time_seconds, time_minutes))

    return length_ids


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def _test(*args):
    while True:
        print("Blabla")
        asyncio.sleep(2)

@bot.command()
async def shutdown(*args):
    await bot.say("Shutting down...")
    await bot.close()

@bot.command()
async def stopaccepting(*args):
    STOP_ACCEPT = True
    await bot.say("Stopped accepting!")
    
@bot.command()
async def setaccept(*args):
    STOP_ACCEPT = False
    await bot.say("Set accepting!")

@bot.command()
async def acceptvv(username, password, threads):
    """Accepts follow requests of instagram account"""
    threads = int(threads)

    api = try_login(username, password)

    if not api:
        await bot.say("Incorrect login credentials!")
        return
    
    await bot.say("Logged in!")

    total_vv = 0
    t0 = time.time()

    while True:
        try:
            status = accept(api, threads)

            if status == 0:
                break

            total_vv += status

            if 7990 < total_vv < 8010:
                await bot.say("Waiting...")
                asyncio.sleep(60 * 6)

            asyncio.sleep(1)

            if STOP_ACCEPT:
                break
        except Exception as e:
            await bot.say(str(e))

    t1 = time.time()
    time_difference = t1 - t0
    time_seconds = round(time_difference, 2)
    time_minutes = round(time_difference / 60, 2)

    print("Everything Took {} Seconds | {} Minutes".format(time_seconds, time_minutes))
    await bot.say("Everything Took {} Seconds | {} Minutes".format(time_seconds, time_minutes))
    print("Total Follow Requests Accepted: {}".format(total_vv))
    await bot.say("Total Follow Requests Accepted: {}".format(total_vv))

@bot.command()
async def add(left : int, right : int):
    """Adds two numbers together."""
    await bot.say(left + right)

@bot.command()
async def roll(dice : str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))

@bot.command()
async def repeat(times : int, content='repeating...'):
    """Repeats a message multiple times."""
    for i in range(times):
        await bot.say(content)

@bot.command()
async def joined(member : discord.Member):
    """Says when a member joined."""
    await bot.say('{0.name} joined in {0.joined_at}'.format(member))

@bot.group(pass_context=True)
async def cool(ctx):
    """Says if a user is cool.
    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await bot.say('No, {0.subcommand_passed} is not cool'.format(ctx))

@cool.command(name='bot')
async def _bot():
    """Is the bot cool?"""
    await bot.say('Yes, the bot is cool.')

bot.run(os.getenv("TOKEN"))
