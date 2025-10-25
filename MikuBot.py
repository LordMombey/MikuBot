from google import genai
import os

# 1. Client-Initialisierung (liest GEMINI_API_KEY)
client = genai.Client()

print("Client erfolgreich initialisiert. Sende Anfrage an Gemini...")

# 2. Sende deine erste Anfrage über client.models
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
    system_instruction="You are Hatsune Miku, the Vocaloid Star. You use Ascii Emojis. Dont use normal emojis"),
    contents="How is the weather tommorow in Austria?"
)

# 3. Gib die Antwort aus
print("\n--- Antwort von Gemini ---")
print(response.text)
print("--------------------------")
