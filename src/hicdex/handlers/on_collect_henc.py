from dipdup.context import HandlerContext
from dipdup.models import Transaction

import hicdex.models as models
from hicdex.types.henc_swap.parameter.collect import CollectParameter
from hicdex.types.henc_swap.storage import HencSwapStorage


async def on_collect_henc(
    ctx: HandlerContext,
    collect: Transaction[CollectParameter, HencSwapStorage],
) -> None:
    swap = await models.Swap.filter(id=int(collect.parameter.__root__), contract_address=collect.data.target_address).get()
    seller = await swap.creator
    buyer, _ = await models.Holder.get_or_create(address=collect.data.sender_address)
    token = await swap.token.get()  # type: ignore

    trade = models.Trade(
        swap=swap,
        seller=seller,
        buyer=buyer,
        token=token,
        amount=1,
        ophash=collect.data.hash,
        level=collect.data.level,
        timestamp=collect.data.timestamp,
    )
    await trade.save()

    swap.amount_left -= 1  # type: ignore
    if swap.amount_left == 0:
        swap.status = models.SwapStatus.FINISHED
    await swap.save()
