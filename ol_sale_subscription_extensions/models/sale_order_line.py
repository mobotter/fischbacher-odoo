from odoo import models
import re


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)

        name = res.get('name', '')
        if not name:
            return res

        lines = [line.strip() for line in name.splitlines() if line.strip()]

        period_re = re.compile(
            r'^\d+\s*(Tag|Tage|Woche|Wochen|Woche\(n\)|Monat|Monate|Monat\(e\))\s*'
            r'\d{2}\.\d{2}\.\d{4}\s+bis\s+\d{2}\.\d{2}\.\d{4}$',
            re.IGNORECASE
        )

        cleaned_lines = [
            line for line in lines
            if not period_re.match(line)
        ]

        res['name'] = '\n'.join(cleaned_lines).strip()
        return res
