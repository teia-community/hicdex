from dipdup.context import HookContext
from dipdup.datasources.datasource import Datasource
from dipdup.enums import ReindexingReason


async def on_index_rollback(
    ctx: HookContext,
    datasource: Datasource,
    from_level: int,
    to_level: int,
) -> None:
    await ctx.execute_sql('on_index_rollback')
    await ctx.reindex(ReindexingReason.rollback)
