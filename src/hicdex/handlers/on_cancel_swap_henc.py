from dipdup.context import HandlerContext
from dipdup.models import Transaction

import hicdex.models as models
from hicdex.types.henc_swap.parameter.cancel_swap import CancelSwapParameter
from hicdex.types.henc_swap.storage import HencSwapStorage


async def on_cancel_swap_henc(
    ctx: HandlerContext,
    cancel_swap: Transaction[CancelSwapParameter, HencSwapStorage],
) -> None:
    swap = await models.Swap.filter(id=int(cancel_swap.parameter.__root__), contract_address=cancel_swap.data.target_address).get()
    swap.status = models.SwapStatus.CANCELED
    swap.level = cancel_swap.data.level  # type: ignore
    await swap.save()
