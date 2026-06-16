from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)

        if self.order_id.is_subscription:
            name = res.get('name', '')
            # Variante 1: Zeilenumbruch (\n)
            if '\n' in name:
                res['name'] = name.split('\n')[0]
            # Variante 2: Datumsmuster entfernen (z.B. "4 Woche(n) 08.06.2026 bis 05.07.2026")
            else:
                import re
                res['name'] = re.sub(
                    r'\s*\d+\s+\w+\([n]\)\s+\d{2}\.\d{2}\.\d{4}\s+bis\s+\d{2}\.\d{2}\.\d{4}',
                    '',
                    name
                ).strip()

        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('name')
    def _remove_subscription_period_from_name(self):
        pass

    def write(self, vals):
        if 'name' in vals and vals['name']:
            import re
            vals['name'] = re.sub(
                r'\n?\d+\s+\w+\(n\)\s+\d{2}\.\d{2}\.\d{4}\s+bis\s+\d{2}\.\d{2}\.\d{4}',
                '',
                vals['name']
            ).strip()
        return super().write(vals)
