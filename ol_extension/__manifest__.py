{
    "name": "Fischbacher Extension",
    "version": "18.0.1.0.0",
    "summary": "A custom module for Fischbacher customization",
    "depends": ["base", "contacts", "stock", "stock_delivery"],
    "author": "Sana Khalid",
    "category": "",
    "data": [
        "security/ir.model.access.csv",
        "reports/report_delivery_document.xml",
        "reports/report_invoice_document.xml",
        "reports/report_saleorder_document.xml",
        "views/res_partner.xml",
        "views/sale_order.xml",
        "views/client_info.xml",
    ],
    "installable": True,
    "application": True,
    # TASK ID: 51580: One of the report (PROFORMA INVOICE sale.order) modifications has directly been implemented from front in odoo studio customization.
    # EXTERNAL ID: studio_customization.web_studio_report_ed_bb9632ba-b884-41fd-b7d0-b3fbd04ced70
}
