# Standard imports
import asyncio
import logging
from typing import Optional

# External imports
from discord import Embed, Member, Message, Reaction
from discord.ext import commands

# Local imports
from utils.configuration import COMMAND_ALIASES, DISABLED_COMMANDS, EMBED_COLOR

log = logging.getLogger('viMusBot')

EMOJI = {
    'cancel': '❌',
    'confirm': '✅',
    'repeat': '🔁',
    'info': 'ℹ️',
    'num': [
        '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟',
    ],
}

def is_command_enabled(ctx: commands.Context) -> bool:
    """Checks whether this command's name is found in the configuration's list of disabled commands."""
    return not ctx.command.name in DISABLED_COMMANDS

def command_aliases(command: str) -> list[str]:
    """Returns a list of aliases for the given command."""
    return COMMAND_ALIASES[command] or []

def embedq(title: str, subtext: Optional[str]=None, color: int=EMBED_COLOR) -> Embed:
    """Shortcut for making embeds for messages."""
    return Embed(title=title, description=subtext, color=color)

async def prompt_for_choice(bot: commands.Bot, ctx: commands.Context,
    prompt_msg: Message,
    yesno: bool=False,
    choice_nums: int=0,
    timeout_seconds: int=30,
    delete_after: bool=True) -> int | asyncio.TimeoutError | ValueError:
    """Adds reactions to a given Message (`prompt_msg`) and returns the outcome.

    Returns the chosen number if a valid selection was made, otherwise a `TimeoutError` if a timeout occurred,\
    a `ValueError` if `choice_nums` was greater than 10, or 0 if the selection was cancelled.

    @prompt_msg: A `Message` containing the choices that will be edited or deleted depending on the outcome.
    @yesno: (`False`) Makes this choice prompt a simple yes/no confirmation with a green checkbox and a cancel button.
        `choice_nums` does not need to be set if this is `True`.
    @choice_nums: (`0`) How many choices to give. Will always start at 1 and end at `choice_nums`.\
        An error will be raised if `yesno` is `False` but `choice_nums` is still the default `0`.\
        Maximum of 10, as that is the highest number an individual emoji can represent.
    @timeout_seconds: (`30`) How long to wait before automatically cancelling the prompt, in seconds.
    @delete_after: (`True`) Whether to delete the choice prompt after either a timeout has occurred,\
        the selection was cancelled, or a valid selection was made.
    """
    # Get reaction menu ready
    log.info('Prompting for reactions...')

    if (not yesno) and (choice_nums == 0):
        raise ValueError('choice_nums must be greater than 0 if this is not a yes/no dialog.')

    if not yesno:
        if choice_nums > len(EMOJI['num']):
            log.debug('Number of choices (%s) out of range for emoji number list.', choice_nums)
            await prompt_msg.edit(embed=embedq(f'Couldn\'t make choice prompt, limit ({len(EMOJI['num'])}) exceeded.'))
            # Returned instead of raised because this could happen as a result of an automated process
            # So the bot can decide what to do with this
            return ValueError('choice_nums can not be greater than 10.')

        for i in range(choice_nums):
            await prompt_msg.add_reaction(EMOJI['num'][i + 1])
    else:
        await prompt_msg.add_reaction(EMOJI['confirm'])
    await prompt_msg.add_reaction(EMOJI['cancel'])

    def check(reaction: Reaction, user: Member) -> bool:
        return user == ctx.message.author and (str(reaction.emoji) in EMOJI['num'] + [EMOJI['confirm']] or str(reaction.emoji) == EMOJI['cancel'])

    log.debug('Waiting for reaction...')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=timeout_seconds, check=check)
    except asyncio.TimeoutError as e:
        log.debug('Choice prompt timeout reached.')
        if delete_after:
            await prompt_msg.delete()
        return e

    log.debug('Received a valid reaction.')

    if str(reaction) == EMOJI['cancel']:
        log.debug('Selection cancelled.')
        if delete_after:
            await prompt_msg.delete()
        return 0

    if str(reaction) == EMOJI['confirm']:
        log.debug('Selection confirmed.')
        if delete_after:
            await prompt_msg.delete()
        return 1

    choice = EMOJI['num'].index(str(reaction))
    log.debug('%s selected.', choice)
    if delete_after:
        await prompt_msg.delete()
    return choice
