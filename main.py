import os
from typing import Final

import discord
from discord.ext import commands, tasks
import google.generativeai as genai
import logging
from discord import Intents, Client, app_commands
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logging.basicConfig(level=logging.INFO)

load_dotenv()

GOOGLE_API_KEY: Final[str] = os.getenv('GOOGLE_API_KEY')
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

genai.configure(api_key=GOOGLE_API_KEY)

default_system_instructions = ("")


class MyClient(commands.Bot):
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
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        })
        self.chats: dict[int: list[str]] = {}
        self.system_instructions: str = default_system_instructions
        self.tree: app_commands.CommandTree = app_commands.CommandTree(self)

        # these are currently hard coded for testing
        self.guild: discord.Object = discord.Object(1249435119379284050)
        self.channel_id = 1254211789605044304

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

    async def on_ready(self):
        logging.info(f'We have logged in as {self.user}')

    async def on_message(self, message: discord.Message):
        author = message.author
        channel = message.channel

        if author.bot or author.system:
            return

        if channel.id != self.channel_id:
            return

        if not self.chats.get(author.id):
            self.chats[author.id] = self.model.start_chat(history=[])

        chat = self.chats.get(author.id)

        try:
            prompt = [f"{self.system_instructions}", f"input: {message.content}", "output: "]
            response = chat.send_message(prompt)

            await message.reply(response.text)
        except Exception as e:
            logging.error(f'{type(e).__name__}: {e}')


intents: Intents = Intents.default()
intents.message_content = True


def main():
    logging.info(f'Starting Discord bot')

    try:
        client = MyClient()

        @client.tree.command()
        async def get(interaction: discord.Interaction):
            """Returns the current system instructions"""
            await interaction.response.send_message(client.system_instructions)

        @client.tree.command()
        async def change(interaction: discord.Interaction, system_instructions: str):
            """Changes the system instructions.

            Parameters
            -----------
            system_instructions: str
                The system instructions
                :param interaction:
            """

            client.system_instructions = system_instructions
            await interaction.response.send_message('Changed the system instructions to "' + system_instructions + '"')

        @client.tree.command()
        async def channel(interaction: discord.Interaction, id: str):
            """Changes the channel.

            Parameters
            -----------
            id: str
                The ID of the channel
            """

            client.channel_id = int(id)
            channel = client.get_channel(client.channel_id)

            await interaction.response.send_message(f'Changed the channel to {channel.mention}')

        @client.tree.command()
        async def reset(interaction: discord.Interaction):
            """Resets the system instructions"""
            client.system_instructions = default_system_instructions
            await interaction.response.send_message(f'Reset the system instructions to {default_system_instructions}')

        @client.tree.command()
        async def clear(interaction: discord.Interaction):
            """Clears the chat history"""
            client.chats = {}
            await interaction.response.send_message('Cleared the chat history')

        client.run(DISCORD_TOKEN)

        logging.info(f'Shutting down Discord bot')
    except Exception as e:
        logging.error(f'Error running the Discord bot: {e}')


if __name__ == '__main__':
    main()
