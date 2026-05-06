from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[('dymo_price','Dymo Price'),('dymo_without_price','Dymo Without Price'),('dymo_artikel_barcode','Dymo Artikel Barcode'), ('dymo_small','Dymo Small'), ('dymo_price_small','Dymo Price Small'),('zpl_small','ZPL Small') ,('zpl_without_price','ZPL WIthOut Price')], 
        ondelete={'dymo_price': 'set default','dymo_without_price': 'set default','dymo_artikel_barcode': 'set default','dymo_price_small': 'set default', 'dymo_small': 'set default', 'zpl_small': 'set default', 'zpl_without_price': 'set default'})

    # Task Id 34020 JC add dymo_without_price selection and if condition
        def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()
        
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
