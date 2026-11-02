# Adds Custom Fields to Contacts

Dieses Modul erweitert `res.partner` um zusätzliche Kontakt- und Steuerfelder und ergänzt optional eine Verkaufssperre für Kunden. Wenn zusätzlich `sale` als Abhängigkeit eingebunden ist, kann das Modul auch `sale.order` erweitern, damit gesperrte Kunden im Verkaufsauftrag nicht auswählbar sind.

## Funktionen

- Steuer-Identifikationsnummer
- Steuernummer
- Telefax
- Supplier Customer Number
- DSP 3 ID
- Verkaufssperre am Kontakt

## Modulstruktur

```text
contact_custom_fields/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── res_partner.py
│   └── sale_order.py
└── views/
    ├── res_partner_views.xml
    └── sale_order_views.xml
```


## Hinweise

- Die Partnerfelder liegen in `models/res_partner.py`.
- Die Verkaufssperre für Aufträge liegt in `models/sale_order.py`.
- Die Formularansichten liegen im Ordner `views/`.
- Daten-Dateien wie XML-Views müssen im Manifest unter `data` eingetragen werden, damit Odoo sie lädt.
