from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[
            ('sep_dymo', '--- PDF / DYMO ETIKETTEN ---'),  # Visuelle Trennung
            ('dymo_price', 'FB Dymo Price (89x36mm)'),
            ('dymo_without_price', 'FB Dymo without Price (89x36mm)'),
            ('dymo_artikel_barcode', 'FB Dymo Artikel Barcode (89x36mm)'),
            ('dymo_small', 'FB Dymo Small (54x25mm)'),
            ('dymo_price_small', 'FB Dymo Price Small (54x25mm)'),
            ('sep_zpl', '--- ZPL / ZEBRA ETIKETTEN---'),     # Visuelle Trennung
            ('zpl_small', 'FB ZPL Zebra small label'),
            ('zpl_without_price', 'FB ZPL Zebra without Price')
        ], 
        ondelete={
            'sep_dymo': 'set default',
            'dymo_price': 'set default',
            'dymo_without_price': 'set default',
            'dymo_artikel_barcode': 'set default',
            'dymo_price_small': 'set default',
            'dymo_small': 'set default',
            'sep_zpl': 'set default',
            'zpl_small': 'set default',
            'zpl_without_price': 'set default'
        }
    )

    def _prepare_report_data(self):
        # 1. SICHERHEITSPRÜFUNG HINZUFÜGEN
        if self.print_format in ['sep_dymo', 'sep_zpl']:
            raise UserError(_("Bitte wählen Sie ein konkretes Etikettenformat aus, keine Überschrift."))

        xml_id, data = super()._prepare_report_data()
        
        # 2. IHR BESTEHENDES MAPPING
        report_mapping = {
            'dymo_price': 'report_dymo_barcode.report_product_template_label_dymo_price',
            'dymo_without_price': 'report_dymo_barcode.report_product_template_label_dymo_without_price',
            'dymo_artikel_barcode': 'report_dymo_barcode.report_product_template_label_dymo_artikel_barcode',
            'dymo_price_small': 'report_dymo_barcode.report_product_template_label_dymo_price_small',
            'dymo_small': 'report_dymo_barcode.report_product_template_label_dymo_small',
            'zpl_small': 'report_dymo_barcode.report_product_template_label_zpl_small',
            'zpl_without_price': 'report_dymo_barcode.report_product_template_label_zpl_without_price'
        }
        
        if self.print_format in report_mapping:
            xml_id = report_mapping[self.print_format]
            
        return xml_id, data
