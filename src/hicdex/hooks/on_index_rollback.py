from os import environ as env

from aiohttp import ClientSession
from dipdup.context import HookContext
from dipdup.index import Index


async def send(levels_diff: int) -> None:
    api_key = env.get('MAILGUN_API_KEY')
    if not api_key:
        return

    to_emails = env.get('NOTIFIED_EMAILS', '').split(',')

    async with ClientSession() as session:
        await session.post(
            "https://api.eu.mailgun.net/v3/mail.hicdex.com/messages",
            auth=("api", api_key),
            data={
                "from": "Hicdex API <mailgun@mail.hicdex.com>",
                "to": to_emails,
                "subject": "Rollback hicdex 3",
                "text": f"Chain reorg: {levels_diff} blocks, please reindex!",
            },
        )


async def on_index_rollback(
    ctx: HookContext,
    index: Index,
    from_level: int,
    to_level: int,
) -> None:
    await send(from_level - to_level)
