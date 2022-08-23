from datetime import datetime
from enum import Enum, IntEnum

from dipdup.models import Model
from tortoise import ForeignKeyFieldInstance, fields


class SwapStatus(IntEnum):
    ACTIVE = 0
    FINISHED = 1
    CANCELED = 2


class ShareholderStatus(str, Enum):
    unspecified = 'unspecified'
    core_participant = 'core_participant'
    benefactor = 'benefactor'


class FA2(Model):
    contract = fields.CharField(36, pk=True)


class Holder(Model):
    address = fields.CharField(36, pk=True)
    name = fields.TextField(default='')
    description = fields.TextField(default='')
    metadata_file = fields.TextField(default='')
    metadata = fields.JSONField(default={})
    hdao_balance = fields.BigIntField(default=0)
    is_split = fields.BooleanField(default=False)


class SplitContract(Model):
    contract: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'shares', index=True)
    administrator = fields.CharField(36, null=True)
    total_shares = fields.BigIntField(null=True)


class Shareholder(Model):
    split_contract: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField(
        'models.SplitContract', 'shareholder', index=True
    )
    holder: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'shareholder', index=True)
    shares = fields.BigIntField()
    holder_type = fields.CharEnumField(ShareholderStatus, default=ShareholderStatus.unspecified)

    holder_id: str


class Token(Model):
    id = fields.BigIntField(pk=True)
    creator: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'tokens', index=True, null=True)
    title = fields.TextField(default='')
    description = fields.TextField(default='')
    artifact_uri = fields.TextField(default='')
    display_uri = fields.TextField(default='')
    thumbnail_uri = fields.TextField(default='')
    metadata = fields.TextField(default='')
    extra = fields.JSONField(default={})
    mime = fields.TextField(default='')
    royalties = fields.SmallIntField(default=0)
    supply = fields.SmallIntField(default=0)
    hdao_balance = fields.BigIntField(default=0)
    is_signed = fields.BooleanField(default=False)

    level = fields.BigIntField(default=0)
    timestamp = fields.DatetimeField(default=datetime.utcnow())

    creator_id: str

    rights = fields.TextField(default='')
    right_uri = fields.TextField(default='')
    formats = fields.JSONField(default={})
    language = fields.TextField(default='')
    attributes = fields.JSONField(default={})

    accessibility = fields.JSONField(default={})
    content_rating = fields.TextField(default='')
    minting_tool = fields.TextField(default='')


class TokenOperator(Model):
    token: ForeignKeyFieldInstance[Token] = fields.ForeignKeyField('models.Token', 'operators', null=False, index=True)
    owner: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'owner', index=True)
    operator = fields.CharField(36)
    level = fields.BigIntField()

    class Meta:
        table = 'token_operator'


class TagModel(Model):
    id = fields.BigIntField(pk=True)
    tag = fields.CharField(255)


class TokenTag(Model):
    token: ForeignKeyFieldInstance[Token] = fields.ForeignKeyField('models.Token', 'token_tags', null=False, index=True)
    tag: ForeignKeyFieldInstance[TagModel] = fields.ForeignKeyField(
        'models.TagModel', 'tag_tokens', null=False, index=True
    )

    class Meta:
        table = 'token_tag'


class TokenHolder(Model):
    holder: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField(
        'models.Holder', 'holders_token', null=False, index=True
    )
    token: ForeignKeyFieldInstance[Token] = fields.ForeignKeyField(
        'models.Token', 'token_holders', null=False, index=True
    )
    quantity = fields.BigIntField(default=0)

    class Meta:
        table = 'token_holder'


class Signatures(Model):
    token: ForeignKeyFieldInstance[Token] = fields.ForeignKeyField(
        'models.Token', 'token_signatures', null=False, index=True
    )
    holder: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField(
        'models.Holder', 'holder_signatures', null=False, index=True
    )

    holder_id: str

    class Meta:
        table = 'split_signatures'
        unique_together = (("token", "holder"),)


class Swap(Model):
    id = fields.BigIntField(index=True)
    creator: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'swaps', index=True)
    token: ForeignKeyFieldInstance[Token] = fields.ForeignKeyField('models.Token', 'swaps', index=True)
    price = fields.BigIntField()
    amount = fields.SmallIntField()
    amount_left = fields.SmallIntField()
    status = fields.IntEnumField(SwapStatus)
    royalties = fields.SmallIntField()
    fa2: ForeignKeyFieldInstance[FA2] = fields.ForeignKeyField('models.FA2', 'swaps', index=True)
    contract_address = fields.CharField(36, index=True)
    contract_version = fields.SmallIntField()
    is_valid = fields.BooleanField(default=True)

    opid = fields.BigIntField(pk=True)
    ophash = fields.CharField(51)
    level = fields.BigIntField()
    timestamp = fields.DatetimeField()


class Trade(Model):
    id = fields.BigIntField(pk=True)
    token: ForeignKeyFieldInstance[Token] = fields.ForeignKeyField('models.Token', 'trades', index=True)
    swap: ForeignKeyFieldInstance[Swap] = fields.ForeignKeyField('models.Swap', 'trades', index=True)
    seller: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'sales', index=True)
    buyer: ForeignKeyFieldInstance[Holder] = fields.ForeignKeyField('models.Holder', 'purchases', index=True)
    amount = fields.BigIntField()

    ophash = fields.CharField(51)
    level = fields.BigIntField()
    timestamp = fields.DatetimeField()


class IgnoredCids(Model):
    cid = fields.CharField(53, pk=True)
