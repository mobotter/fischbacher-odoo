# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Adds Custom Fields to Products',
    'author': 'Odolution',
    'depends': ['sale','website_sale'],
    'data': [
        'views/product_form.xml',
        'views/product_search.xml',
        'views/product_attribute.xml',
        'views/category.xml',
        'views/menu.xml',
        "security/ir.model.access.csv",
    ],
    'external_dependencies': {
    },
    'license': 'LGPL-3',
}
