"""Cog for general, miscellaneous commands."""

# Standard imports
import logging

# External imports
from discord.ext import commands

# Local imports
from cogs.common import command_aliases, embedq, is_command_enabled
from version import VERSION

log = logging.getLogger('lydian')

class General(commands.Cog):
    """General, miscellaneous functions."""
    def __init__(self, bot: commands.bot.Bot):
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
        await ctx.send(embed=embedq('viMusBot GitHub repository: https://github.com/svioletg/viMusBot',
            'https://github.com/svioletg/viMusBot\nA GitHub account is required to submit issues.'))

    @commands.command(aliases=command_aliases('faq'))
    @commands.check(is_command_enabled)
    async def faq(self, ctx: commands.Context):
        """Returns a link to viMusBot's FAQ page."""
        await ctx.send(embed=embedq('viMusBot FAQ page: https://github.com/svioletg/viMusBot/blob/master/docs/faq.md'))

    @commands.command(aliases=command_aliases('issues'))
    @commands.check(is_command_enabled)
    async def issues(self, ctx: commands.Context):
        """Returns a link to viMusBot's FAQ page."""
        await ctx.send(embed=embedq('viMusBot Issues page: https://github.com/svioletg/viMusBot/issues'))
