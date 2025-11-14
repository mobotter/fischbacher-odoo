from odoo import models,api,fields,_
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    def split_by_limit(self,text, limit):
        words = text.split()
        result = []
        current = ""
    
        for w in words:
            if len(current) + len(w) + (1 if current else 0) <= limit:
                current += (" " if current else "") + w
            else:
                result.append(current)
                current = w
    
        if current:
            result.append(current)
        
        if len(result) > 2:
            result = result[:2]
    
        return result