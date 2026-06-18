from odoo import api, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Helper utility - statische Methode, keine Odoo-Abhängigkeit
    @staticmethod
    def split_by_limit(text, limit):
        """
        Zerlegt langen Text in Wörterblöcke, begrenzt auf maximal 2 Linien.
        
        Args:
            text: Der zu zerlegende Text
            limit: Maximale Länge pro Linie
            
        Returns:
            Liste mit maximal 2 Textblöcke
        """
        if not text:
            return []
        
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
        
        # Begrenzen auf maximal 2 Linien
        if len(result) > 2:
            result = result[:2]
    
        return result

    @api.depends('default_code', 'name')
    def _compute_display_name(self):
        for product in self:
            name = product.name or ''
            product.display_name = f"{product.default_code} - {name}" if product.default_code else name

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            args = ['|', ('default_code', operator, name), ('name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def name_create(self, name):
        if self.env.context.get('forbid_quick_create_product'):
            raise UserError(_("Das Anlegen neuer Produkte aus dieser Produktsuche ist nicht erlaubt."))
        return super().name_create(name)
