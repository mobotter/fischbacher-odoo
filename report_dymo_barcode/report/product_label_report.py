# report/product_label_report.py

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from collections import defaultdict


class ReportProductTemplateLabelBase(models.AbstractModel):
    """Gemeinsame Basisklasse für alle Dymo/ZPL Label-Reports."""
    _name = 'report.report_dymo_barcode.base'  # Nicht in ir.actions.report registriert!
    _description = 'Base Report for Dymo/ZPL Labels'

    def _prepare_common_data(self, docids, data, include_price=False):
        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        active_model = data.get('active_model')

        if active_model == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif active_model == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                'pricelist': layout_wizard.pricelist_id if include_price and layout_wizard else None,
                'price_included': include_price,
                'extra_html': layout_wizard.extra_html if layout_wizard else "",
            }
        else:
            raise UserError(_('Product model not defined. Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product', {})
        product_ids = [int(p) for p in qty_by_product_in.keys()]
        products = Product.search([('id', 'in', product_ids)], order='name desc')
        quantity_by_product = defaultdict(list)

        for product in products:
            q = qty_by_product_in.get(str(product.id), 1)
            quantity_by_product[product].append((product.barcode, q))
            total += q

        if data.get('custom_barcodes'):
            for product_id, barcodes_qtys in data.get('custom_barcodes').items():
                browsed_product = Product.browse(int(product_id))
                if browsed_product.exists():
                    quantity_by_product[browsed_product].extend(barcodes_qtys)
                    total += sum(qty for _, qty in barcodes_qtys)

        page_numbers = (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1 if total else 1

        result = {
            'quantity': quantity_by_product,
            'page_numbers': page_numbers,
            'extra_html': layout_wizard.extra_html or "",
        }
        if include_price:
            result['price_included'] = data.get('price_included', False)
            result['pricelist'] = layout_wizard.pricelist_id

        return result


class ReportProductTemplateLabelDymoPrice(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_price'
    _inherit = 'report.report_dymo_barcode.base'  # ← ERBT jetzt _prepare_common_data
    _description = 'Product Label Report Dymo Price'

    def _get_report_values(self, docids, data):
        return self._prepare_common_data(docids, data, include_price=True)


class ReportProductTemplateLabelDymoWithOutPrice(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_without_price'
    _inherit = 'report.report_dymo_barcode.base'
    _description = 'Product Label Report Dymo Without Price'

    def _get_report_values(self, docids, data):
        return self._prepare_common_data(docids, data, include_price=False)


class ReportProductTemplateLabelDymoArtikelBarcode(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_artikel_barcode'
    _inherit = 'report.report_dymo_barcode.base'
    _description = 'Product Label Report Dymo Artikel Barcode'

    def _get_report_values(self, docids, data):
        return self._prepare_common_data(docids, data, include_price=False)


class ReportProductTemplateLabelDymoPriceSmall(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_price_small'
    _inherit = 'report.report_dymo_barcode.base'
    _description = 'Product Label Report Dymo Price Small'

    def _get_report_values(self, docids, data):
        return self._prepare_common_data(docids, data, include_price=True)


class ReportProductTemplateLabelDymoSmall(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_small'
    _inherit = 'report.report_dymo_barcode.base'
    _description = 'Product Label Report Dymo Small'

    def _get_report_values(self, docids, data):
        return self._prepare_common_data(docids, data, include_price=False)
