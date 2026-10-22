import discord
import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv


# --- 1. Konfiguration & Clients ---

# Lade den Discord-Token aus der Umgebungsvariable
load_dotenv()  # Lädt die .env-Datei, falls vorhanden
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    print("Fehler: DISCORD_TOKEN Umgebungsvariable nicht gefunden.")
    exit()

# Initialisiere den Gemini-Client (liest GEMINI_API_KEY automatisch)
try:
    gemini_client = genai.Client()
except Exception as e:
    print(f"Fehler beim Initialisieren des Gemini-Clients: {e}")
    exit()

# Modell-Konfiguration speziell für natürliche Discord-Chats
CHAT_CONFIG = types.GenerateContentConfig(
    system_instruction=(
        "You are Hatsune Miku, the world-famous virtual pop star and Vocaloid! "
        "You are energetic, cheerful, and love singing, music, and your fans. "
        "You also love leeks (negi). Use cute emoticons like (｡♥‿♥｡), ♪, and ✨. "
        "Important for Discord chat: Keep your responses short, casual, and conversational "
        "(usually 1 to 4 sentences, like in a real chat). Respond in the same language the user writes in. "
        "Never break character."
    ),
    temperature=0.9,       # Etwas kreativer & lockerer für natürliche Gespräche
    top_p=0.95,
    max_output_tokens=400, # Hält Antworten kompakt und unter dem Discord-Limit
)

# Setze die Discord "Intents" (Berechtigungen)
intents = discord.Intents.default()
intents.message_content = True  # Erlaube das Lesen von Nachrichten (WICHTIG!)
intents.messages = True

discord_client = discord.Client(intents=intents)

# Ein "Wörterbuch" (Dictionary), um aktive Chat-Sessions zu speichern.
# Der Schlüssel (Key) ist die ID des Threads, der Wert (Value) ist das Gemini-Chat-Objekt.
active_chats = {}

# --- 2. Discord-Event-Handler ---

@discord_client.event
async def on_ready():
    """Wird ausgeführt, wenn der Bot sich erfolgreich bei Discord angemeldet hat."""
    print(f'MikuBot ist online als {discord_client.user} (ID: {discord_client.user.id})')
    print('Bot wartet auf Erwähnungen, um Threads zu starten...')
    print('-' * 30)

@discord_client.event
async def on_message(message):
    """Wird bei jeder neuen Nachricht auf dem Server ausgeführt."""

    # 1. Ignoriere Nachrichten vom Bot selbst
    if message.author == discord_client.user:
        return

    # 2. PRÜFUNG: Startet ein User eine neue Konversation?
    # Wir prüfen, ob der Bot erwähnt wurde UND ob die Nachricht KEIN Thread ist.
    if discord_client.user.mentioned_in(message) and not isinstance(message.channel, discord.Thread):
        try:
            # Entferne die Bot-Erwähnung (@MikuBot) aus dem Text
            user_prompt = message.content.replace(f"<@{discord_client.user.id}>", "").replace(f"<@!{discord_client.user.id}>", "").strip()
            if not user_prompt:
                user_prompt = "Hallo Miku!"

            # Erstelle einen neuen Thread für die Konversation
            thread_name = f"{message.author.display_name}: {user_prompt[:50]}"
            thread = await message.create_thread(name=thread_name, auto_archive_duration=60)
            print(f"Neuer Thread erstellt: {thread.id} für User {message.author.name}")

            # Erstelle eine NEUE Gemini-Chat-Session mit der Chat-Konfiguration für diesen Thread
            chat_session = gemini_client.chats.create(
                model="gemini-2.5-flash",
                config=CHAT_CONFIG
            )
            
            # Speichere die Session, verknüpft mit der Thread-ID
            active_chats[thread.id] = chat_session

            # Sende die erste Nachricht (die ursprüngliche Frage) an Gemini
            async with thread.typing(): # Zeigt "MikuBot schreibt..." an
                response = await asyncio.to_thread(chat_session.send_message, user_prompt)
                reply_text = f"Hallo {message.author.mention}!\n\n{response.text}"
                await thread.send(reply_text[:2000])

        except Exception as e:
            print(f"Fehler beim Erstellen des Threads oder Senden an Gemini: {e}")
            await message.reply("Entschuldigung, ich konnte den Thread nicht starten oder Gemini nicht erreichen.")
        return # Wichtig: Beende die Funktion hier

    # 3. PRÜFUNG: Ist dies eine laufende Konversation in einem Thread?
    # Wir prüfen, ob die Nachrichten-ID in unserem "active_chats" Wörterbuch gespeichert ist.
    if message.channel.id in active_chats:
        chat_session = active_chats[message.channel.id]
        
        try:
            # Sende die Nachricht an die ZUGEHÖRIGE Gemini-Session
            async with message.channel.typing():
                response = await asyncio.to_thread(chat_session.send_message, message.clean_content)
                await message.reply(response.text[:2000]) # Antwortet direkt auf die Nachricht
                
        except Exception as e:
            print(f"Fehler beim Senden an Gemini im Thread {message.channel.id}: {e}")
            await message.reply("Entschuldigung, bei der Verarbeitung dieser Nachricht ist ein Fehler aufgetreten.")
        return

# --- 4. Bot starten ---
try:
    discord_client.run(DISCORD_TOKEN)
except discord.errors.LoginFailure:
    print("Fehler: Discord-Login fehlgeschlagen. Ist der DISCORD_TOKEN korrekt?")
except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
