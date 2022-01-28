import discord
import requests
from datetime import date
from datetime import timedelta
from ratelimit import limits, sleep_and_retry
import re
import json
import os
import random

EIGHT_SECONDS = 8

client = discord.Client()
token = os.environ.get("DISCORD_BOT_TOKEN")
channel_id = os.environ.get("DISCORD_CHANNEL_ID")
pattern = re.compile(r"Wordle\s(\d+)\s([X\d])/6")

X_WEIGHT = 8

black_tokens = ["<:dealwithit:909637718131228712>", "<:babyPunch:866867781378375690>", "<:disappoint:806271529796894780>",
    "<:michaelcera:802781343926321173>", "<:thisguy:917530795663585280>", "<:PUGGERS:921828086234886215>", "<:Squidge:936486390777135174>"]
yellow_tokens = ["<:fieri:820478494462705705>", "<:pika:804160423922368566>", "<:justright:803699314220072993>", "<:AngySponge:876638662664790036>", "<:elmo:803074047565889566>", "<:swtf:936111196032082000>"]
green_tokens = ["<:hmm:848946269133209610>", "<:pepeknife:802342853460099082>", "<:monkaW:921828961774895144>", 
    "<:Pepega:921828917403344927>", "<:POGGERS:803702292075249695>", "<:POGGERSDOWN:803702045906698261>", "<:Bradge:922902962718801971>", 
    "<:HYPERS:921829124870381680>", "<:PepeHands:921828724012359701>", "<:orly:936468871756525569>"]

black_square = b"\xe2\xac\x9b"
white_square = b"\xe2\xac\x9c"
yellow_square = b"\xf0\x9f\x9f\xa8"
green_square = b"\xf0\x9f\x9f\xa9"

# wordle: {
#   num: {
#       avg: x
        # num: x
        # total: x
        # date: x
# }
# 
# }
# author_id: {
#  name
#  stats: {
#   wordle: 1-7 (x weight to 7)
#  }
# current_stat
# total_num
# current_total
# }

wordle = {

}

stats = {

}

def get_previous_week():
    days_to_get = date.today().weekday() + 1
    prevous_week = days_to_get + 7
    current_wordle = 0
    today = date.today()
    yesterday = today - timedelta(days = 1)
    for key, value in wordle.items():
        if(value['date'] == today.strftime("%d%m%Y")):
            current_wordle = int(key)
            break
        elif(value['date'] == yesterday.strftime("%d%m%Y")):
            current_wordle = int(key) + 1
            break

    return_wordles = []
    for i in range(days_to_get, prevous_week):
        return_wordles.append(int(current_wordle) - int(i))
    print(return_wordles)
    return return_wordles

def get_week():
    days_to_get = date.today().weekday() + 1
    current_wordle = 0
    today = date.today()
    yesterday = today - timedelta(days = 1)
    for key, value in wordle.items():
        if(value['date'] == today.strftime("%d%m%Y")):
            current_wordle = int(key)
            break
        elif(value['date'] == yesterday.strftime("%d%m%Y")):
            current_wordle = int(key) + 1
            break

    return_wordles = []
    for i in range(0, days_to_get):
        return_wordles.append(int(current_wordle) - int(i))

    return return_wordles

def get_stats_for_week(week):
    temp = {}
    for key, value in stats.items():
        total = 0
        amount = 0
        missed = 0
        name = value['name']
        for wordle_num in week:
            if(str(wordle_num) in value['stats']):
                total += 1
                amount += value['stats'][str(wordle_num)]
            else:
                total += 1
                missed += 1
                amount += 8

        # for wordle_num in value['stats']:
        #     if(int(wordle_num) in week):
        #         total += 1
        #         amount += value['stats'][wordle_num]
        #     else:
        #         total += 1
        #         missed += 1
        #         amount += 8

        if(total != 0):
            current_stat = amount/total
            if(missed == 0):
                temp[current_stat+(random.random()/1000000)] = "%s - Average: %s, Total: %s\n" % (name, str(round(current_stat, 2)), str(total))
            else:
                temp[current_stat+(random.random()/1000000)] = "%s - Average: %s, Total: %s, Missed: %s\n" % (name, str(round(current_stat, 2)), str(total-missed), str(missed))

    ordered_list = sorted(temp.keys())

    i = 1
    return_str = ""
    for key in ordered_list:
        return_str += "%d. %s" % (i, temp[key])
        i += 1

    return return_str

def is_valid_token(c, black_token, yellow_token, green_token):
    if(c == black_square or c == white_square):
        return black_token
    elif(c == yellow_square):
        return yellow_token
    elif(c == green_square):
        return green_token
    else:
        return None

def generate_new_hidden_puzzle(puzzle):
    random.seed(random.random())
    black_token = random.choice(black_tokens)
    yellow_token = random.choice(yellow_tokens)
    green_token = random.choice(green_tokens)
    word_length = 5
    i = 0
    to_return = ""
    for c in puzzle:
        character = c.encode('utf-8')
        token = is_valid_token(character, black_token, yellow_token, green_token)
        if(token):
            to_return += token
            i += 1

        if (i == word_length):
            to_return += "\n"
            i = 0

    return to_return

def is_wordle_comment(comment):
    return pattern.search(comment)

def new_valid_comment(author_id, name, match):
    wordle_number = match.group(1)
    wordle_value = 7 if match.group(2) == "X" else int(match.group(2))

    if(not (author_id in stats)):
        stats[author_id] = {
            "name": name,
            "stats": {},
            "current_stat": 0,
            "total_num": 0,
            "current_total": 0
        }

    if(not (wordle_number in wordle)):
        wordle[wordle_number] = {
            "average": 0,
            "number": 0,
            "total": 0,
            "date": date.today().strftime("%d%m%Y")
        }

    if(not (wordle_number in stats[author_id]["stats"])):
        wordle[wordle_number]["number"] += wordle_value
        wordle[wordle_number]["total"] += 1
        wordle[wordle_number]["average"] += wordle[wordle_number]["number"] / wordle[wordle_number]["total"]

        stats[author_id]["name"] = name
        stats[author_id]["stats"][wordle_number] = wordle_value
        stats[author_id]["total_num"] += 1
        stats[author_id]["current_total"] += wordle_value
        stats[author_id]["current_stat"] = stats[author_id]["current_total"]/stats[author_id]["total_num"]

def print_stats(id):
    return_str = "%s stats:\n" % stats[id]['name']
    for key, value in sorted(stats[id]['stats'].items()):
        return_str += "%s - %s\n" % (key, value)

    return return_str

def print_rank():
    temp = {}
    for key, value in stats.items():
        temp[value['current_stat']+(random.random()/1000000)] = "%s - Average: %s, Total: %s\n" % (value['name'], str(round(value['current_stat'], 2)), str(value['total_num']))

    ordered_list = sorted(temp.keys())

    i = 1
    return_str = ""
    for key in ordered_list:
        return_str += "%d. %s" % (i, temp[key])
        i += 1

    return return_str

def get_help():
    return_str = "Wordle-Bot help:\n"
    return_str += "!join - this will add you to the current wordle thread.\n"
    return_str += "!help - display help information\n"
    return_str += "!rank - display server rankings\n"
    return_str += "!rng - reply rng to a wordle result and it will output a randomly generated tile of your wordle results.\n"
    return_str += "!week - display this weeks server rankings\n"
    return_str += "!previousweek - display the previous weeks server rankings\n"
    return_str += "!stats <id> - right click user and \"Copy Id\" to get the user's id and display their stats\n"
    return_str += "Putting your wordle daily share in the chat will add it to the stats and then add you to the thread.\n"

    return return_str

@sleep_and_retry
@limits(calls=5, period=EIGHT_SECONDS)
def get_all_channel_messages_before(channel_id, id=0):
    if(id != 0):
        headers = {
            "Authorization" : "Bot %s" % token
        }
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages?before={id}"
    else :
        headers = {
            "Authorization" : "Bot %s" % token
        }
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"

    r = requests.get(url, headers=headers)
    
    return r.json()

def get_all_channel_messages(channel_id):
    r_json = get_all_channel_messages_before(channel_id)
    
    before_id = r_json[-1]['id']
    while r_json:
        for item in r_json:
            match = is_wordle_comment(item['content'])
            if(match):
                new_valid_comment(item['author']['id'], item['author']['username'], match)

        r_json = get_all_channel_messages_before(channel_id, before_id)

        if not r_json:
            break
        before_id = r_json[-1]['id']

async def create_thread(self,name,minutes):
    headers = {
        "Authorization" : "Bot %s" % token
    }
    url = f"https://discord.com/api/v9/channels/{self.id}/threads"
    data = {
        "name" : name,
        "type" : 11,
        "auto_archive_duration" : minutes,
        "invitable": True
    }

    r = requests.post(url,headers=headers,json=data)
    print(r)
    r_json = r.json()
    return r_json['id']

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if str(message.channel.id) == channel_id:
        match = is_wordle_comment(message.content)
        if message.content.startswith('!join') or match:
            today = date.today()
            d1 = today.strftime("%d%m%Y")
            thread_name = "Wordle %s" % d1
            thread_id = await message.channel.check_thread(name=thread_name)
            if(not thread_id):
                thread_id = await message.channel.create_thread(name=thread_name, minutes=1440)

            # await message.channel.send(f"<@{user_id}> is the best")
            await message.channel.add_member_to_thread(thread_id=thread_id, author_id=message.author.id)
        
        if match:
            new_valid_comment(str(message.author.id), message.author.name, match)
            
        if message.content.startswith('!rng') and message.reference is not None:
            reply_message = await message.channel.fetch_message(message.reference.message_id)
            await message.channel.send(generate_new_hidden_puzzle(reply_message.content), reference=message)

        if message.content.startswith('!rank'):
            await message.channel.send(print_rank())

        if message.content.startswith('!stats'):
            id = message.content.split(" ")[1]
            await message.channel.send(print_stats(id))

        if message.content == '!help':
            await message.channel.send(get_help())

        if message.content.startswith('!week'):
            week = get_week()
            await message.channel.send(get_stats_for_week(week))

        if message.content.startswith('!previousweek'):
            week = get_previous_week()
            await message.channel.send(get_stats_for_week(week))


    print('Message from {0.author}: {0.content}'.format(message))

async def check_thread(self, name):
    headers = {
        "Authorization" : "Bot %s" % token
    }
    url = f"https://discord.com/api/v9/channels/{self.id}/threads/active"


    r = requests.get(url, headers=headers)
    data = r.json()
    for thread in data['threads']:
        if(thread['name'] == name):
            return thread['id']

    return None

async def add_member_to_thread(self, thread_id, author_id):
    headers = {
        "Authorization" : "Bot %s" % token
    }
    url = f"https://discord.com/api/v9/channels/{thread_id}/thread-members/{author_id}"


    r = requests.put(url, headers=headers)

discord.TextChannel.create_thread = create_thread
discord.TextChannel.check_thread = check_thread
discord.TextChannel.add_member_to_thread = add_member_to_thread
get_all_channel_messages(channel_id)
client.run(token)