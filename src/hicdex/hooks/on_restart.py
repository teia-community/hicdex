from dipdup.context import HookContext

from hicdex.metadata_utils import fix_holder_metadata, fix_other_metadata


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql('on_restart')
