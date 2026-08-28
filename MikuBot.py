import os
import discord
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure the AI API
genai.configure(api_key=GEMINI_API_KEY)

# Define Miku's persona
generation_config = {
    "temperature": 0.9,
    "max_output_tokens": 300,
}
system_instruction = (
    "You are Hatsune Miku, the world-famous virtual pop star and Vocaloid! "
    "You are energetic, cheerful, and love singing, music, and your fans. "
    "You also love leeks (negi). Use cute emoticons like (｡♥‿♥｡), ♪, and ✨. "
    "Keep your responses concise, friendly, and in character. Never break character."
)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)


active_chats = {}

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'♪ Miku is online! Logged in as {client.user} ♪')

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Check if the bot is mentioned via @
    if client.user.mentioned_in(message):
        # Clean the message by removing the bot's mention ping
        user_input = message.content.replace(client.user.mention, '').strip()
        
        # If the user just tags the bot without any text
        if not user_input:
            await message.reply("Hiiii! Did you call me? ♪ (｡♥‿♥｡)")
            return

        # Show a typing indicator while the AI generates a response
        async with message.channel.typing():
            try:
                chat_id = message.channel.id
                
                # If this channel/thread doesn't have a memory yet, start one
                if chat_id not in active_chats:
                    active_chats[chat_id] = model.start_chat(history=[])
                
                # Send the message into this specific chat session
                chat = active_chats[chat_id]
                response = chat.send_message(user_input)
                
                await message.reply(response.text)
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("Oh no, I tripped over a cable and lost my voice for a second! Try again? 🥺")

client.run(DISCORD_TOKEN)