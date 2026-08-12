{
    'name': 'Order Line Search',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'author': 'Moritz Kern',
    'maintainer': 'Moritz Kern',
    'website': 'https://github.com/Fischbacher-GmbH-Co-KG/odoo/tree/main/order_line_search',
    'summary': 'Erweiterte Ansicht und Smart-Buttons für alle Auftragspositionen inkl. Margen- und Routenprüfung',
    'description': """
Order Line Search & Reporting
=============================

Dieses Modul erweitert das Odoo-Verkaufsmodul um eine flache, detaillierte Ansicht aller Auftragspositionen (Sale Order Lines).
Es ermöglicht Vertriebsmitarbeitern eine schnelle Recherche direkt auf Positionsebene, ohne sich durch einzelne Verkaufsaufträge klicken zu müssen.

**Hauptfunktionen:**
* **Zentraler Menüpunkt:** Unter *Verkauf -> Berichtswesen -> Auftragszeilen*.
* **Smart-Buttons:** Neue Schnellzugriffe bei Kunden (res.partner) und Produkten (product.template/product.product), um sofort alle zugehörigen Auftragspositionen aufzulisten.
* **Erweiterte Spalten:** Die Listenansicht zeigt auf einen Blick wichtige Details wie Verkaufsdatum, Rabatt, Verkaufspreis, den hinterlegten Einkaufspreis des Produkts sowie die gewählte Logistik-Route (z. B. Streckengeschäft).
* **Quick-Actions:** Über klickbare Icons am Ende jeder Zeile kann sofort in das jeweilige Produkt, den Kunden oder den Originalauftrag gesprungen werden.
* **Optimierte Suche:** Direkte Suchfunktion nach Artikelnummern (Interne Referenz) und Kunden in der Suchleiste.

Die Listenansichten öffnen sich standardmäßig ungruppiert (flach), um eine datums- und auftragsübergreifende Analyse zu erleichtern.
    """,
    'depends': [
        'base',
        'sale', 
        'sale_management',
        'sale_stock',
    ],
    'data': [
        'views/sale_order_line_menu.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
