from odoo import models, api

class Base(models.AbstractModel):
    _inherit = "base"

    @classmethod
    def _patch_method(cls, name, method):
        origin = getattr(cls, name)
        method.origin = origin
        # propagate decorators from origin to method, and apply api decorator
        wrapped = api.propagate(origin, method)
        wrapped.origin = origin
        setattr(cls, name, wrapped)
