import discord
import os
import asyncio
from google import genai

# --- 1. Konfiguration & Clients ---

# Lade den Discord-Token aus der Umgebungsvariable
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
async def on_message("You are Hatsune Miku, the Vocaloid Star. You use Ascii Emojis. Dont use normal emojis. React to the following message:" + message):
    """Wird bei jeder neuen Nachricht auf dem Server ausgeführt."""

    # 1. Ignoriere Nachrichten vom Bot selbst
    if message.author == discord_client.user:
        return

    # 2. PRÜFUNG: Startet ein User eine neue Konversation?
    # Wir prüfen, ob der Bot erwähnt wurde UND ob die Nachricht KEIN Thread ist.
    if discord_client.user.mentioned_in(message) and not isinstance(message.channel, discord.Thread):
        try:
            # Erstelle einen neuen Thread für die Konversation
            thread_name = f"Chat mit {message.author.display_name}"
            # Wir nehmen den ersten Teil der Nachricht als Start des Thread-Namens
            if message.clean_content:
                thread_name = f"{message.author.display_name}: {message.clean_content[:50]}..."
                
            thread = await message.create_thread(name=thread_name, auto_archive_duration=60)
            print(f"Neuer Thread erstellt: {thread.id} für User {message.author.name}")

            # Erstelle eine NEUE Gemini-Chat-Session für diesen Thread
            chat_session = gemini_client.chats.create(model="gemini-2.5-flash")
            
            # Speichere die Session, verknüpft mit der Thread-ID
            active_chats[thread.id] = chat_session

            # Sende die erste Nachricht (die ursprüngliche Frage) an Gemini
            async with thread.typing(): # Zeigt "MikuBot schreibt..." an
                response = chat_session.send_message(message.clean_content)
                await thread.send(f"Hallo {message.author.mention}! Hier ist deine Antwort:\n\n{response.text}")

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
                response = chat_session.send_message(message.clean_content)
                await message.reply(response.text) # Antwortet direkt auf die Nachricht
                
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
