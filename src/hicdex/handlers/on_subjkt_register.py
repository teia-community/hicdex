import logging
from typing import Dict

from dipdup.context import HandlerContext
from dipdup.enums import MessageType
from dipdup.models import Transaction

import hicdex.models as models
from hicdex.metadata_utils import fetch_metadata_ipfs
from hicdex.types.hen_subjkt.parameter.registry import RegistryParameter
from hicdex.types.hen_subjkt.storage import HenSubjktStorage
from hicdex.utils import fromhex

_logger = logging.getLogger(__name__)


async def on_subjkt_register(
    ctx: HandlerContext,
    registry: Transaction[RegistryParameter, HenSubjktStorage],
) -> None:
    addr = registry.data.sender_address
    _logger.info(f'{addr}')
    holder, _ = await models.Holder.get_or_create(address=addr)

    name = fromhex(registry.parameter.subjkt)
    _logger.info(f'{name}')
    metadata_file = fromhex(registry.parameter.metadata)
    _logger.info(f'{metadata_file}')
    metadata: Dict[str, str] = {}

    holder.name = name
    holder.metadata_file = metadata_file
    holder.metadata = metadata

    level = ctx.get_tzkt_datasource("tzkt_mainnet").get_channel_level(MessageType.head)
    if registry.data.level > level - 200 and metadata_file.startswith('ipfs://'):
        _logger.info("Fetching IPFS metadata")
        holder.metadata = await fetch_metadata_ipfs(ctx, holder.metadata_file)
    else:
        _logger.info("Skipping metadata fetch")

    holder.description = holder.metadata.get('description', '')

    await holder.save()
