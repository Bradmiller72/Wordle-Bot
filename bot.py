import discord
import requests
from datetime import date
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

X_WEIGHT = 7

#
# author_id: {
#  name
#  stats: {
#   wordle: 1-7 (x weight to 7)
#  }
# current_stat
# total_num
# current_total
# }

stats = {

}

def is_wordle_comment(comment):
    return pattern.match(comment)

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

    if(not (wordle_number in stats[author_id]["stats"])):
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

        if message.content.startswith('!rank'):
            await message.channel.send(print_rank())

        if message.content.startswith('!stats'):
            id = message.content.split(" ")[1]
            await message.channel.send(print_stats(id))

        if message.content.startswith('!help'):
            await message.channel.send(get_help())


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