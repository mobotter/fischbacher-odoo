# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from .. import odoorpc


def _slug(v):
    if isinstance(v, odoorpc.models.BaseModel):
        return v.id
    if isinstance(v, int):
        return v
    if not v:
        return False
    if isinstance(v, (tuple, list)) and len(v) > 1:
        return v[0]
    return v
