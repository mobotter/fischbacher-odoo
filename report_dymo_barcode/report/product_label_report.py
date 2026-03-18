from odoo import _, api, fields, models
from odoo.exceptions import UserError
from collections import defaultdict
import markupsafe

class ReportProductTemplateLabelDymoPrice(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_price'
    _description = 'Product Label Report Dymo Price'

    def _get_report_values(self, docids, data):
        return self._prepare_data(docids, data)



    def _prepare_data(self, docids, data):
        # change product ids by actual product object to get access to fields in xml template
        # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            # special case: users trying to customize labels
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                'pricelist': layout_wizard.pricelist_id,
            }
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product')
        # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
        # is LIFO, which results in ordering by product name in the report
        products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
        quantity_by_product = defaultdict(list)
        for product in products:
            q = qty_by_product_in[str(product.id)]
            quantity_by_product[product].append((product.barcode, q))
            total += q
        if data.get('custom_barcodes'):
            # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
                total += sum(qty for _, qty in barcodes_qtys)

        return {
            'quantity': quantity_by_product,
            'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
            'price_included': data.get('price_included'),
            'extra_html': layout_wizard.extra_html,
            'pricelist': layout_wizard.pricelist_id,
        }
# Task id 34020 JC
class ReportProductTemplateLabelDymoWithOutPrice(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_without_price'
    _description = 'Product Label Report Dymo With Out Price'

    def _get_report_values(self, docids, data):
        return self._prepare_data(docids, data)


    def _prepare_data(self, docids, data):
        # change product ids by actual product object to get access to fields in xml template
        # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            # special case: users trying to customize labels
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                # 'pricelist': layout_wizard.pricelist_id,
            }
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product')
        # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
        # is LIFO, which results in ordering by product name in the report
        products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
        quantity_by_product = defaultdict(list)
        for product in products:
            q = qty_by_product_in[str(product.id)]
            quantity_by_product[product].append((product.barcode, q))
            total += q
        if data.get('custom_barcodes'):
            # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
                total += sum(qty for _, qty in barcodes_qtys)

        return {
            'quantity': quantity_by_product,
            'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
            'price_included': data.get('price_included'),
            'extra_html': layout_wizard.extra_html,
            # 'pricelist': layout_wizard.pricelist_id,
        }
# Task id 34020 JC

# Task id 34092 JC
class ReportProductTemplateLabelDymoArtikelBarcode(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_artikel_barcode'
    _description = 'Product Label Report Dymo Artikel Barcode'

    def _get_report_values(self, docids, data):
        return self._prepare_data(docids, data)


    def _prepare_data(self, docids, data):
        # change product ids by actual product object to get access to fields in xml template
        # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            # special case: users trying to customize labels
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                # 'pricelist': layout_wizard.pricelist_id,
            }
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product')
        # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
        # is LIFO, which results in ordering by product name in the report
        products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
        quantity_by_product = defaultdict(list)
        for product in products:
            q = qty_by_product_in[str(product.id)]
            quantity_by_product[product].append((product.barcode, q))
            total += q
        if data.get('custom_barcodes'):
            # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
                total += sum(qty for _, qty in barcodes_qtys)

        return {
            'quantity': quantity_by_product,
            'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
            'price_included': data.get('price_included'),
            'extra_html': layout_wizard.extra_html,
            # 'pricelist': layout_wizard.pricelist_id,
        }
# Task id 34092 JC
class ReportProductTemplateLabelDymoPriceSmall(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_price_small'
    _description = 'Product Label Report Dymo Price Small'

    def _get_report_values(self, docids, data):
        return self._prepare_data(docids, data)



    def _prepare_data(self, docids, data):
        # change product ids by actual product object to get access to fields in xml template
        # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            # special case: users trying to customize labels
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                'pricelist': layout_wizard.pricelist_id,
            }
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product')
        # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
        # is LIFO, which results in ordering by product name in the report
        products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
        quantity_by_product = defaultdict(list)
        for product in products:
            q = qty_by_product_in[str(product.id)]
            quantity_by_product[product].append((product.barcode, q))
            total += q
        if data.get('custom_barcodes'):
            # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
                total += sum(qty for _, qty in barcodes_qtys)

        return {
            'quantity': quantity_by_product,
            'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
            'price_included': data.get('price_included'),
            'extra_html': layout_wizard.extra_html,
            'pricelist': layout_wizard.pricelist_id,
        }

class ReportProductTemplateLabelDymoSmall(models.AbstractModel):
    _name = 'report.report_dymo_barcode.dymo_small'
    _description = 'Product Label Report Dymo Small'

    def _get_report_values(self, docids, data):
        return self._prepare_data(docids, data)



    def _prepare_data(self, docids, data):
        # change product ids by actual product object to get access to fields in xml template
        # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            # special case: users trying to customize labels
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                'pricelist': layout_wizard.pricelist_id,
            }
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product')
        # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
        # is LIFO, which results in ordering by product name in the report
        products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
        quantity_by_product = defaultdict(list)
        for product in products:
            q = qty_by_product_in[str(product.id)]
            quantity_by_product[product].append((product.barcode, q))
            total += q
        if data.get('custom_barcodes'):
            # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
                total += sum(qty for _, qty in barcodes_qtys)

        return {
            'quantity': quantity_by_product,
            'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
            'price_included': data.get('price_included'),
            'extra_html': layout_wizard.extra_html,
            'pricelist': layout_wizard.pricelist_id,
        }

class ReportProductLabel(models.AbstractModel):
    _inherit = 'report.stock.label_product_product_view'

    def _get_report_values(self, docids, data):
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template']
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product']
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        quantity_by_product = defaultdict(list)
        for p, q in data.get('quantity_by_product').items():
            product = Product.browse(int(p))
            default_code_markup = markupsafe.Markup(product.default_code) if product.default_code else ''
            product_info = {
                'barcode': markupsafe.Markup(product.barcode) if product.barcode else '',
                'quantity': q,
                'display_name_markup': markupsafe.Markup(product.display_name),
                'default_code': (default_code_markup[:15], default_code_markup[15:30]),
                'name': markupsafe.Markup(product.name)
            }
            quantity_by_product[product].append(product_info)
        if data.get('custom_barcodes'):
            # we expect custom barcodes to be: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                product = Product.browse(int(product))
                default_code_markup = markupsafe.Markup(product.default_code) if product.default_code else ''
                for barcode_qty in barcodes_qtys:
                    quantity_by_product[product].append({
                        'barcode': markupsafe.Markup(barcode_qty[0]),
                        'quantity': barcode_qty[1],
                        'display_name_markup': markupsafe.Markup(product.display_name),
                        'default_code': (default_code_markup[:15], default_code_markup[15:30]),
                        'name': markupsafe.Markup(product.name)
                    }
                    )
        data['quantity'] = quantity_by_product
        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        data['pricelist'] = layout_wizard.pricelist_id

        return data

class ReportProductLabelSmall(models.AbstractModel):
    _name = 'report.stock.label_product_product_view_small'

    def _get_report_values(self, docids, data):
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template']
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product']
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        quantity_by_product = defaultdict(list)
        for p, q in data.get('quantity_by_product').items():
            product = Product.browse(int(p))
            default_code_markup = markupsafe.Markup(product.default_code) if product.default_code else ''
            product_info = {
                'barcode': markupsafe.Markup(product.barcode) if product.barcode else '',
                'quantity': q,
                'display_name_markup': markupsafe.Markup(product.display_name),
                'default_code': (default_code_markup[:15], default_code_markup[15:30]),
                'name': markupsafe.Markup(product.name)
            }
            quantity_by_product[product].append(product_info)
        if data.get('custom_barcodes'):
            # we expect custom barcodes to be: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                product = Product.browse(int(product))
                default_code_markup = markupsafe.Markup(product.default_code) if product.default_code else ''
                for barcode_qty in barcodes_qtys:
                    quantity_by_product[product].append({
                        'barcode': markupsafe.Markup(barcode_qty[0]),
                        'quantity': barcode_qty[1],
                        'display_name_markup': markupsafe.Markup(product.display_name),
                        'default_code': (default_code_markup[:15], default_code_markup[15:30]),
                        'name': markupsafe.Markup(product.name)
                    }
                    )
        data['quantity'] = quantity_by_product
        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        data['pricelist'] = layout_wizard.pricelist_id

        return data

# Task id 34163 JC 
class ReportZplProductWithOutPrice(models.AbstractModel):
    _name = 'report.report_dymo_barcode.zpl_without_price'
    _description = 'Product Label Report Zpl With Out Price'

    def _get_report_values(self, docids, data):
        return self._prepare_data(docids, data)


    def _prepare_data(self, docids, data):
        # change product ids by actual product object to get access to fields in xml template
        # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)

        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if data.get('active_model') == 'product.template':
            Product = self.env['product.template'].with_context(display_default_code=False)
        elif data.get('active_model') == 'product.product':
            Product = self.env['product.product'].with_context(display_default_code=False)
        elif data.get("studio") and docids:
            # special case: users trying to customize labels
            products = self.env['product.template'].with_context(display_default_code=False).browse(docids)
            quantity_by_product = defaultdict(list)
            for product in products:
                quantity_by_product[product].append((product.barcode, 1))
            return {
                'quantity': quantity_by_product,
                'page_numbers': 1,
                # 'pricelist': layout_wizard.pricelist_id,
            }
        else:
            raise UserError(_('Product model not defined, Please contact your administrator.'))

        if not layout_wizard:
            return {}

        total = 0
        qty_by_product_in = data.get('quantity_by_product')
        # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
        # is LIFO, which results in ordering by product name in the report
        products = Product.search([('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
        quantity_by_product = defaultdict(list)
        for product in products:
            q = qty_by_product_in[str(product.id)]
            quantity_by_product[product].append((product.barcode, q))
            total += q
        if data.get('custom_barcodes'):
            # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
            for product, barcodes_qtys in data.get('custom_barcodes').items():
                quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
                total += sum(qty for _, qty in barcodes_qtys)

        return {
            'quantity': quantity_by_product,
            'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
            'price_included': data.get('price_included'),
            'extra_html': layout_wizard.extra_html,
            # 'pricelist': layout_wizard.pricelist_id,
        }
# Task id 34163 JC 