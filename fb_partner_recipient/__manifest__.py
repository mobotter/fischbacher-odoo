{
    "name": "Leistungsempfänger (Partner Recipient)",
    "summary": "Neuer Kontakttyp 'Leistungsempfänger' und Feld partner_recipient_id "
               "in Angeboten/Aufträgen, Lieferscheinen und Rechnungen",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "author": "Moritz Kern",
    "maintainer": "Moritz Kern",
    "company": "Fischbacher GmbH + Co. KG",
    "license": "LGPL-3",
    "depends": ["sale_stock", "account"],
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
}
