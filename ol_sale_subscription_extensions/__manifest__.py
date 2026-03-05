{
    "name": "Sale Subscription Fischbacher Extension",
    "version": "18.0.1.0.0",
    "summary": "A custom module for Fischbacher customization",
    "depends": [
        "base",
        "sale",
        "stock",
        "ol_invoice_report_changes",
        "sale_subscription",
        "mail",

    ],
    "author": "Johi Chawla",
    "category": "",
    "data": [
        "security/ir.model.access.csv",
        "reports/report_action.xml",
        "reports/sale_subscription_report.xml",
        "data/mail_template_data.xml",
        "views/sale_subscription_view.xml",
        "views/sale_order.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "sequence" : -1,
}
