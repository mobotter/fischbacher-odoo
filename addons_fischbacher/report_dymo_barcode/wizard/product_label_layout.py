from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'
    

    print_format = fields.Selection(
        selection_add=[('dymo_price','Dymo Price'),('dymo_without_price','Dymo Without Price'), ('dymo_small','Dymo Small'), ('dymo_price_small','Dymo Price Small'),('zpl_small','ZPL Small')], 
        ondelete={'dymo_price': 'set default','dymo_without_price': 'set default','dymo_price_small': 'set default', 'dymo_small': 'set default', 'zpl_small': 'set default'})

    # Task Id 34020 JC add dymo_without_price selection and if condition
    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()
        if self.print_format == 'dymo_price':
            xml_id = 'report_dymo_barcode.report_product_template_label_dymo_price'
        # task id 34020 JC
        if self.print_format == 'dymo_without_price':
            xml_id = 'report_dymo_barcode.report_product_template_label_dymo_without_price'
        # task id 34020 JC
        if self.print_format == 'dymo_price_small':
            xml_id = 'report_dymo_barcode.report_product_template_label_dymo_price_small'
        if self.print_format == 'dymo_small':
            xml_id = 'report_dymo_barcode.report_product_template_label_dymo_small'
        if self.print_format ==  'zpl_small':
            xml_id = 'report_dymo_barcode.label_product_product_view_small'  
        return xml_id, data