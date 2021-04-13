import demo_quipuswap.models as models
from demo_quipuswap.types.fa2_token.parameter.transfer import Transfer
from demo_quipuswap.types.quipu_fa2.parameter.token_to_tez_payment import TokenToTezPayment
from dipdup.models import HandlerContext, OperationContext


async def on_fa2_token_to_tez(
    ctx: HandlerContext,
    token_to_tez_payment: OperationContext[TokenToTezPayment],
    transfer: OperationContext[Transfer],
) -> None:
    ...