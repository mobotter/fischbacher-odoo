from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    def split_by_limit(self, text, limit):
        if not text:
            return []
            
        words = str(text).split()
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
    
        return result
