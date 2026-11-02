# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductCustom(models.Model):
    _inherit = "product.product"

    search_term = fields.Char("Search Term")
    short_term = fields.Char("Short Term")
    is_rental_available = fields.Boolean("Is Rental Available")
    dsp3_id = fields.Char("DSP 3 ID")
    bonus_applicable = fields.Boolean("Bonus Applicable")
    special_sale_applicable = fields.Boolean("Special Sale Applicable")
    manufacturer_number = fields.Char("Manufacturer Number")

    main_supplier_id = fields.Many2one(
        "product.supplierinfo",
        "Main Supplier",
        compute="_compute_supplier",
        store=True,
    )
    main_supplier_product_number = fields.Char(
        "Main Supplier Product Number",
        compute="_compute_supplier",
        store=True,
    )

    # Product Attributes
    webshop_link = fields.Char("Webshop Link")
    external_id = fields.Integer("External ID")
    length = fields.Char("Length")
    width = fields.Char("Width")
    height = fields.Char("Height")
    brand_id = fields.Many2one("product.brand", "Brand")

    product_website_product_attribute_ids = fields.One2many(
        "product.website.attribute.product",
        "product_id",
        "Website Attribute Values",
    )
    product_website_attribute_ids = fields.Many2many(
        "product.website.attribute",
        string="Website Attributes",
    )

    # Vermietung
    inspection_date = fields.Date("Inspection Date")
    uvv_date = fields.Date("UVV Date")
    brake_inspection_date = fields.Date("Brake Inspection Date")

    @api.depends(
        "seller_ids",
        "seller_ids.product_code",
        "seller_ids.partner_id",
        "seller_ids.price",
    )
    def _compute_supplier(self):
        for rec in self:
            if rec.seller_ids:
                main_supplier = rec.seller_ids[0]
                rec.main_supplier_id = main_supplier
                rec.main_supplier_product_number = main_supplier.product_code
            else:
                rec.main_supplier_id = False
                rec.main_supplier_product_number = False

    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        return super().name_search(
            name=name,
            domain=domain,
            operator=operator,
            limit=limit,
        )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        # Der sichtbare lst_price der Variantenansicht stammt technisch
        # aus product.template.list_price.
        values["list_price"] = 9999.99

        return values


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Model to allow a Product Brand"
    _rec_name = "name"

    name = fields.Char("Name")
    image = fields.Image("Image")
    external_id = fields.Integer("External ID")


class ProductImage(models.Model):
    _inherit = "product.image"
    _description = "Product Image extension for External ID Mapping"

    external_id = fields.Integer("External ID")


class ProductWebsiteAttribute(models.Model):
    _name = "product.website.attribute"
    _description = "Model to allow non Variant Creating Attributes"
    _rec_name = "name"

    name = fields.Char("Name")
    external_id = fields.Integer("External ID")
    sequence = fields.Integer("Sequence")
    visible = fields.Boolean("Visible")

    option_ids = fields.One2many(
        "product.website.attribute.value",
        "attribute_id",
        "Options",
    )


class ProductWebsiteAttributeValue(models.Model):
    _name = "product.website.attribute.value"
    _description = "Model to allow non Variant Creating Attribute Values"
    _rec_name = "name"

    name = fields.Char("Name")
    external_id = fields.Integer("External ID")

    attribute_id = fields.Many2one(
        "product.website.attribute",
        "Attribute",
        ondelete="cascade",
    )


class ProductWebsiteAttributeProduct(models.Model):
    _name = "product.website.attribute.product"
    _description = "Website Attribute for Products"

    product_id = fields.Many2one(
        "product.product",
        "Product",
        required=True,
        ondelete="cascade",
    )
    attribute_id = fields.Many2one(
        "product.website.attribute",
        "Attribute",
        required=True,
        ondelete="cascade",
    )
    value_ids = fields.Many2many(
        "product.website.attribute.value",
        "product_website_attribute_value_product",
        "attribute_value_id",
        "product_id",
        "Values",
    )
