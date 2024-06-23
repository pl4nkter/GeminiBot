import os
from typing import Final

import discord
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from discord import Intents, Client, app_commands
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: Final[str] = os.getenv('GOOGLE_API_KEY')
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

genai.configure(api_key=GOOGLE_API_KEY)

GUILD = discord.Object(id=1254176270871298118)
default_system_instructions = "You are a teenager that uses Gen Z slang and doesn't capitalize their sentences."


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
        self.chats: dict[int: list[str]] = {}
        self.system_instructions: str = default_system_instructions
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: discord.Message):
        author = message.author
        channel = message.channel

        if author.bot or author.system:
            return

        if channel.id != 1254201882692419665:
            return

        if not self.chats.get(author.id):
            self.chats[author.id] = self.model.start_chat(history=[])

        chat = self.chats.get(author.id)

        try:
            prompt = [f"{self.system_instructions}", f"input: {message.content}", "output: "]
            response = chat.send_message(prompt)

            await message.reply(response.text)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')


intents: Intents = Intents.default()
intents.message_content = True


def main():
    client = MyClient()

    @client.tree.command()
    async def get_system_instructions(interaction: discord.Interaction):
        """Clears the message history"""
        await interaction.response.send_message(client.system_instructions)

    @client.tree.command()
    async def change_system_instructions(interaction: discord.Interaction, system_instructions: str):
        """Changes the system instructions.

        Parameters
        -----------
        system_instructions: str
            The system instructions
        """

        client.system_instructions = system_instructions
        await interaction.response.send_message('Changed the system instructions to "' + system_instructions + '"')

    @client.tree.command()
    async def reset_system_instructions(interaction: discord.Interaction):
        """Resets the system instructions"""
        client.system_instructions = default_system_instructions
        await interaction.response.send_message('Reset the system instructions to default')

    @client.tree.command()
    async def clear(interaction: discord.Interaction):
        """Clears the chat history"""
        client.chats = {}
        await interaction.response.send_message('Cleared the chat history')

    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
