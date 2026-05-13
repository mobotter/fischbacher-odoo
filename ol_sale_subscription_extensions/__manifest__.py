{
    "name": "Sale Subscription Fischbacher Extension",
    "version": "19.0.1.0.0",
    "summary": "A custom module for Fischbacher customization",
    "author": "Johi Chawla",
    "category": "Sales",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale_management",
        "stock",
        "sale_subscription", 
        "mail"
    ],
    'assets': {
        'web.assets_backend': [
            'ol_sale_subscription_extensions/static/src/js/quotation_line_description_field.js',
            'ol_sale_subscription_extensions/static/src/xml/quotation_line_description_field.xml',
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "reports/report_action.xml",
        "reports/sale_subscription_report.xml",
        "data/mail_template_data.xml",
        "views/sale_subscription_view.xml",
        'views/sale_order_template_view.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": -1,
}
