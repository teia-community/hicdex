
from dipdup.enums import ReindexingReason
from dipdup.datasources.datasource import Datasource
from dipdup.context import HookContext

async def on_index_rollback(
    ctx: HookContext,
    datasource: Datasource,
    from_level: int,
    to_level: int,
) -> None:
    await ctx.execute_sql('on_index_rollback')
    await ctx.reindex(ReindexingReason.rollback)

