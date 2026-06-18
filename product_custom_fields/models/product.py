from odoo import api, fields, models, _

class ProductCustom(models.Model):
    _inherit = 'product.product'

    search_term = fields.Char("Search Term")
    short_term = fields.Char("Short Term")
    is_rental_available = fields.Boolean("Is Rental Available")
    dsp3_id = fields.Char("DSP 3 ID")
    bonus_applicable = fields.Boolean("Bonus Applicable")
    special_sale_applicable = fields.Boolean("Special Sale Applicable")
    manufacturer_number = fields.Char("Manufacturer Number")
    main_supplier_id = fields.Many2one("product.supplierinfo","Main Supplier", compute="_compute_supplier", store=True)
    main_supplier_product_number = fields.Char("Main Supplier Product Number", compute="_compute_supplier", store=True)

    # Product Attributes
    webshop_link = fields.Char("Webshop Link")
    external_id = fields.Integer("External ID")
    length = fields.Char("Length")
    width = fields.Char("Width")
    height = fields.Char("Height")
    brand_id = fields.Many2one("product.brand","Brand")
    product_website_product_attribute_ids = fields.One2many("product.website.attribute.product","product_id","Website Attribute Values")
    product_website_attribute_ids  = fields.Many2many("product.website.attribute", string="Website Attributes")

    #Vermietung
    inspection_date = fields.Date("Inspection Date")
    uvv_date = fields.Date("UVV Date")
    brake_inspection_date = fields.Date("Brake Inspection Date")    

    @api.depends("seller_ids", "seller_ids.product_code", "seller_ids.partner_id", "seller_ids.price")
    def _compute_supplier(self):
        for rec in self:
            if rec.seller_ids:
                ms = rec.seller_ids[0]
                rec.main_supplier_id = ms.partner_id.id
                rec.main_supplier_product_number = ms.product_code
            else:
                rec.main_supplier_id = False
                rec.main_supplier_product_number = False

    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])        
        if name:            
            args += ['|', '|','|','|', ('name', operator, name), ('default_code', operator, name), ('description_sale', operator, name), ('search_term', operator, name), ('short_term', operator, name)]
        return super().name_search(name, args, operator, limit)


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Model to allow a Product Brand"
    _rec_name = "name"
    
    name = fields.Char("Name")
    image = fields.Image("Image")
    external_id = fields.Integer("External ID")


class ProductImage(models.Model):
    _inherit = "product.image"
    _description = "Product Image extension for External ID Mappping"

    external_id = fields.Integer("External ID")


class ProductWebsiteAttribute(models.Model):
    _name = "product.website.attribute"
    _description = "Model to allow non Variant Creating Attributes"
    _rec_name = "name"

    name = fields.Char("Name")
    external_id = fields.Integer("External ID")
    sequence = fields.Integer("Sequence")
    visible = fields.Boolean("Visible")
    option_ids = fields.One2many("product.website.attribute.value", "attribute_id", "Options")


class ProductWebsiteAttributeValue(models.Model):
    _name = "product.website.attribute.value"
    _description = "Model to allow non Variant Creating Attributes Values"
    _rec_name = "name"

    name = fields.Char("Name")
    external_id = fields.Integer("External ID")
    attribute_id = fields.Many2one("product.website.attribute", "Attribute")


class ProductWebsiteAttributeProduct(models.Model):
    _name = "product.website.attribute.product"
    _description = "Website Attribute for Products"

    product_id = fields.Many2one("product.product","Product")
    attribute_id = fields.Many2one("product.website.attribute","Attribute")
    value_ids = fields.Many2many("product.website.attribute.value", "product_website_attribute_value_product", "attribute_value_id", "product_id", "Values")
