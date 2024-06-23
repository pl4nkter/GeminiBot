import os
from typing import Final

import discord
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from discord import Intents, Client
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: Final[str] = os.getenv('GOOGLE_API_KEY')
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

genai.configure(api_key=GOOGLE_API_KEY)


class MyClient(Client):
    def __init__(self) -> None:
        super().__init__(
            command_prefix='~',
            intents=intents,
            help_command=None,
        )
        self.model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        })
        self.chats = {}

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        author = message.author
        channel = message.channel

        if author.bot or author.system:
            return

        if channel.id != 1254211789605044304:
            return

        if not self.chats.get(author.id):
            self.chats[author.id] = self.model.start_chat(history=[])

        chat = self.chats.get(author.id)

        try:
            response = chat.send_message(["system instructions: you are very romantic and you only speak turkish.",
                                          f"input: {message.content}", "output: "])

            # response = chat.send_message(message.content)

            await message.reply(response.text)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')


intents: Intents = Intents.default()
intents.message_content = True  # NOQA


def main():
    client = MyClient()
    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
