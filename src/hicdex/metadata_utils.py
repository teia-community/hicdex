import json
import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
from dipdup.context import DipDupContext
from tortoise.expressions import Q

import hicdex.models as models
from hicdex.utils import clean_null_bytes, http_request

_logger = logging.getLogger(__name__)


async def fix_token_metadata(ctx: DipDupContext, token: models.Token) -> bool:
    metadata = await get_metadata(ctx, token)
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    if isinstance(metadata, bytes):
        return False

    token.title = get_name(metadata)
    token.description = get_description(metadata)
    token.artifact_uri = get_artifact_uri(metadata)
    token.display_uri = get_display_uri(metadata)
    token.thumbnail_uri = get_thumbnail_uri(metadata)
    token.mime = get_mime(metadata)
    token.extra = metadata.get('extra', {})
    token.rights = get_rights(metadata)
    token.right_uri = get_right_uri(metadata)
    token.formats = metadata.get('formats', {})
    token.language = get_language(metadata)
    token.attributes = metadata.get('attributes', {})
    if token.attributes is None:
        token.attributes = {}
    token.content_rating = get_content_rating(metadata)
    token.accessibility = metadata.get('accessibility', {})
    await add_tags(token, metadata)
    await token.save()
    return metadata != {}


async def fix_subjkt_metadata(ctx: DipDupContext, holder: models.Holder) -> bool:
    metadata = await fetch_metadata_ipfs(ctx, holder.metadata_file)
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    if isinstance(metadata, bytes):
        _logger.warning(f'invalid metadata: {metadata}')
        return False

    holder.metadata = metadata
    holder.description = metadata.get('description', {})

    await holder.save()
    return metadata != {}


async def fix_other_metadata(ctx: DipDupContext) -> None:
    _logger.info(f'running fix_missing_metadata job')
    async for token in models.Token.filter(Q(artifact_uri='') | Q(rights__isnull=True)).order_by('-id'):
        if models.IgnoredCids.get_or_none(cid=token.metadata) is None:
            fixed = await fix_token_metadata(ctx, token)
            if fixed:
                _logger.info(f'fixed metadata for {token.id}')
            else:
                _logger.warning(f'failed to fix metadata for {token.id}')
                # insert into ignored_cids path
                await models.IgnoredCids.create(cid=token.metadata)
        else:
            _logger.warning(f'ignoring {token.metadata} for token {token.id}')


async def fix_holder_metadata(ctx: DipDupContext) -> None:
    async for holder in models.Holder.filter(~Q(metadata_file='') & Q(metadata='{}')):
        if models.IgnoredCids.get_or_none(cid=holder.metadata_file) is None:
            fixed = await fix_subjkt_metadata(ctx, holder)
            if fixed:
                _logger.info(f'fixed metadata for {holder.address}')
            else:
                _logger.warning(f'failed to fix metadata for {holder.address}')
                # insert into ignored_cids path
                await models.IgnoredCids.create(cid=holder.metadata_file)
        else:
            _logger.warning(f'ignoring {holder.metadata_file} for holder {holder.address}')


async def add_tags(token: models.Token, metadata: Dict[str, Any]) -> None:
    tags = [await get_or_create_tag(tag) for tag in get_tags(metadata)]
    for tag in tags:
        token_tag = await models.TokenTag(token=token, tag=tag)
        await token_tag.save()


async def get_or_create_tag(tag: str) -> models.TagModel:
    tag_model, _ = await models.TagModel.get_or_create(tag=tag)
    return tag_model


async def get_metadata(ctx: DipDupContext, token: models.Token) -> Dict[str, Any]:
    # FIXME: hard coded contract
    metadata_datasource = ctx.get_metadata_datasource('metadata')
    metadata = await metadata_datasource.get_token_metadata('KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton', token.id)
    if metadata is not None:
        _logger.info(f'found metadata for {token.id} from metadata_datasource')
        return metadata

    data = await fetch_metadata_ipfs(ctx, token.metadata)
    if data != {}:
        _logger.info(f'found metadata for {token.id} from IPFS')
    else:
        data = await fetch_metadata_bcd(ctx, token)
        if data != {}:
            _logger.info(f'metadata for {token.id} from BCD')

    return data


async def fetch_metadata_bcd(ctx: DipDupContext, token: models.Token) -> Dict[str, Any]:
    api = ctx.get_http_datasource('bcd')
    data = await api.request(
        method='get',
        url=f'tokens/mainnet/metadata?contract:KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9&token_id={token.id}',
        weight=1,  # ratelimiter leaky-bucket drops
    )

    data = [
        obj
        for obj in data
        if 'symbol' in obj and (obj['symbol'] == 'OBJKT' or obj['contract'] == 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton')
    ]

    with suppress(FileNotFoundError):
        if data and not isinstance(data[0], list):
            return data[0]
    return {}


async def call_ipfs(ctx: DipDupContext, provider: str, path: str) -> Dict[str, Any]:
    ipfs_datasource = ctx.get_ipfs_datasource(provider)
    data = await ipfs_datasource.get(path.replace('ipfs://', ''))
    if data and not isinstance(data, list):
        return data
    return {}


async def fetch_metadata_ipfs(ctx: DipDupContext, path: str) -> Dict[str, Any]:
    if not path.startswith('ipfs://'):
        return {}

    try:
        _logger.info(f'trying main ipfs url')
        return await call_ipfs(ctx, 'ipfs', path.replace('ipfs://', ''))
    except Exception as e:
        _logger.warning(f'error during ipfs call: {e}')
        try:
            _logger.info(f'trying fallback ipfs url')
            return await call_ipfs(ctx, 'fallback_ipfs', path.replace('ipfs://', ''))
        except Exception as e:
            _logger.warning(f'fallback also borked: {e}')
            try:
                _logger.warning(f'last one')
                return await call_ipfs(ctx, 'fallback2_ipfs', path.replace('ipfs://', ''))
            except Exception as e:
                _logger.warning(f'giving up')

    return {}


def get_mime(metadata: Dict[str, Any]) -> str:
    if ('formats' in metadata) and metadata['formats'] and ('mimeType' in metadata['formats'][0]):
        return metadata['formats'][0]['mimeType']
    return ''


def get_tags(metadata: Dict[str, Any]) -> List[str]:
    tags = metadata.get('tags', [])
    cleaned = [clean_null_bytes(tag) for tag in tags]
    lowercased = [tag.lower() for tag in cleaned]
    uniqued = list(set(lowercased))
    return [tag for tag in uniqued if len(tag) < 255]


def get_name(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('name', ''))


def get_rights(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('rights', ''))


def get_content_rating(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('contentRating', ''))


def get_language(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('language', ''))


def get_description(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('description', ''))


def get_artifact_uri(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('artifact_uri', '') or metadata.get('artifactUri', ''))


def get_display_uri(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('display_uri', '') or metadata.get('displayUri', ''))


def get_thumbnail_uri(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('thumbnail_uri', '') or metadata.get('thumbnailUri', ''))


def get_right_uri(metadata: Dict[str, Any]) -> str:
    return clean_null_bytes(metadata.get('right_uri', '') or metadata.get('rightUri', ''))
