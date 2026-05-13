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
