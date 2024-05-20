# Standard imports
from logging import Logger
from typing import Any, Optional

# External imports
from discord.ext import commands

# Local imports
from cogs.shared import command_aliases, is_command_enabled, embedq
from version import VERSION

class General(commands.Cog):
    """General, miscellaneous functions."""
    def __init__(self, bot: commands.bot.Bot, logger: Logger):
        self.bot = bot

    @commands.command(aliases=command_aliases('changelog'))
    @commands.check(is_command_enabled)
    async def changelog(self, ctx: commands.Context):
        """Returns a link to the changelog, and displays most recent version."""
        await ctx.send(embed=embedq('Read the latest changelog here: https://github.com/svioletg/viMusBot/blob/master/docs/changelog.md', 
            f'This bot is currently running on v{VERSION}'))

    @commands.command(aliases=command_aliases('ping'))
    @commands.check(is_command_enabled)
    async def ping(self, ctx: commands.Context):
        """Test command."""
        await ctx.send('Pong!')
        await ctx.send(embed=embedq('PingPong!', 'PongPing!'))

    @commands.command(aliases=command_aliases('repository'))
    @commands.check(is_command_enabled)
    async def repository(self, ctx: commands.Context):
        """Returns the link to the viMusBot GitHub repository."""
        await ctx.send(embed=embedq('You can view the bot\'s code and submit bug reports or feature requests here.', 
            'https://github.com/svioletg/viMusBot\nA GitHub account is required to submit issues.'))
