import openai
import discord
from datetime import datetime
import xml.etree.ElementTree as ET
import json

class ServerData:
  def __init__(self, id, tokens, month):
    self.id = id
    self.tokens = tokens
    self.month = month

  def toXML(self):
    root = ET.Element("server")
    ET.SubElement(root, "id").text = str(self.id)
    ET.SubElement(root, "tokens").text = str(self.tokens)
    ET.SubElement(root, "month").text = str(self.month)

    return root

  def fromXML(element):
    id = int(element.find("id").text)
    token = int(element.find("tokens").text)
    month = int(element.find("month").text)

    return ServerData(id, token, month)

# Set the OpenAI API key
openai.api_key = "KEY"

# Create a new Discord client
client = discord.Client(intents=discord.Intents.all())

# Define a function that sends a request to GPT-3 and returns the response
async def get_response(prompt):

  # Use the Completion endpoint to generate a response
  response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=prompt,
    max_tokens=1024,
    temperature=1
  )

  response = json.loads(json.dumps(response))
  # Return the response
  return response

storage = {}

def writeXML():
  root = ET.Element("data")

  for value in storage.values():
    root.append(value.toXML())
    
  tree = ET.ElementTree(root)

  with open("data.xml", "wb") as f:
    tree.write(f, encoding='utf-8')

def fill():
  with open("data.xml", "r") as f:

        root = ET.fromstring(f.read())
        servers = root.findall("server")
        for element in servers:
          e = ServerData.fromXML(element)
          storage[e.id] = e

def log(message):
  with open("log.txt", "a") as f:
    f.write(message + '\n')

def paginate(message, chars=2000):
  messages = []
  m = ""
  for char in message:
      if len(m) >= chars:
          messages.append(m)
          m = ""
      m = m + char
  messages.append(m)
  return messages

@client.event
async def on_ready():
  try:
    fill()
  except:
    storage["0"] = ServerData(0, 0, 0)
    writeXML()
    fill()

# Define an event handler for when a message is sent in the Discord chat
@client.event
async def on_message(message):
  # Check if the message is from the bot itself
  if message.author == client.user:
    return

  # Get the server that the message was sent in
  server = message.guild

  # If the server is not in the data, add it with default values
  if server.id not in storage.keys():
    storage[server.id] = ServerData(server.id, 0, datetime.now().month)

  # If the current month is not the same as the last time the token usage was reset, reset the usage
  if storage[server.id].month != datetime.now().month:
    storage[server.id].month[server.id] = (0, datetime.now().month)

  if message.content.strip() == "!tokens":
    await message.channel.send(str(storage[server.id].tokens))

  # If the message starts with the "!gpt3" command, send a request to GPT-3
  if message.content.startswith("!wow"):
    # Get the prompt from the message
    prompt = message.content[5:]
    log(str(datetime.now()) + ": " + server.name + "- " + message.author.name + "> " + prompt)

    # Check if the server has reached its monthly limit of tokens
    if storage[server.id].tokens > 65000 and message.author.id != 464020633253314560:
      await message.channel.send("Sorry, this server has reached its monthly limit of GPT-3 tokens.")
      return

    # Send a request to GPT-3 and get the response
    response = await get_response(prompt.strip())

    # Increment the number of tokens used by the server
    storage[server.id].tokens += int(response["usage"]["total_tokens"])
    

    # Send the response back to the Discord chat
    if len(response["choices"][0]["text"]) > 2000:
      messages = paginate(response["choices"][0]["text"])
      for m in messages:
        await message.channel.send(m)
    else:
      await message.channel.send(response["choices"][0]["text"])
    
    log(str(datetime.now()) + ": " + server.name + "- " + message.author.name + "> " + response["choices"][0]["text"])

    writeXML()

# Start the Discord client - set Discord bot key 
client.run("KEY")
