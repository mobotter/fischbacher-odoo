Point of Sale Customizations
============================

Übersicht
---------

Dieses Modul erweitert den Odoo Point of Sale (POS) um projektspezifische Funktionen. Es bietet insbesondere:

- **Kasse öffnen**: Button zum Öffnen des Geldkastens (Cash Drawer)
- **Artikelnummer anzeigen**: Internal Reference (``default_code``) ganz oben auf jeder Produktkarte
- **Doppelter BON-Druck**: Sofortiger 2x Druck der Rechnung ohne Delay

Technische Details
------------------

- Technischer Name: ``pos_customization``
- Name: ``Point of Sale Customizations``
- Version: ``19.0.1.0.2``
- Author: ``Moritz Kern``
- Kategorie: ``Sales/Point of Sale``
- Sequence: ``40``
- Lizenz: ``LGPL-3``
- Abhängigkeiten: ``point_of_sale``, ``web``, ``base``
- Application: ``True``
- Installable: ``True``

Funktionsumfang
---------------

1. Kasse öffnen (Cash Drawer)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Was: Button in der POS-Control-Buttons-Leiste zum Öffnen des Geldkastens.

Wie:

- Patcht ``ControlButtons.prototype`` (JavaScript OWL-Module)
- ``openDrawer()`` Methode greift auf ``this.pos.hardwareProxy.printer.openCashbox()``
- Fallback auf ``this.pos.hardwareProxy.openCashbox()`` wenn kein Printer
- Console-Warnung wenn Hardware Proxy nicht konfiguriert

UI:

- Button mit Icon (``fa fa-expand``)
- Text: "Kasse öffnen"
- Klasse: ``btn btn-secondary btn-lg py-5``

2. Internal Reference auf Produktkarte
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Was: ``default_code`` (Artikelnummer) wird ganz oben auf jeder Produktkarte angezeigt.

Wie:

- Patcht ``ProductCard`` Template (OWL XML)
- XPath vor ``//div[hasclass('product-img')]``
- ``t-if="props.product.default_code"`` bedingt Anzeige
- Klasse: ``w-100 px-2 py-1 text-muted fw-bold bg-light``
- Style: ``font-size: 0.85em; text-align: center; border-bottom: 1px solid #dee2e6; border-top-left-radius: 5px; border-top-right-radius: 5px;``

UI:

- Kopfzeile auf jeder Karte (ganz oben)
- Grau-heller Hintergrund (``bg-light``)
- Dunkler Text (``text-muted``)
- Fett (``fw-bold``)
- Zentriert
- Mit unterer Border

3. Doppelter BON-Druck
^^^^^^^^^^^^^^^^^^^^^^

Was: Nach erfolgreichem Rechnungsdruck wird **sofort** ein zweites BON gedruckt (ohne Delay).

Wie:

- Patcht ``PaymentScreen.prototype.validateOrder()``
- Nach ``await super.validateOrder()``
- Zwei sequentielle Druckbefehle:

  - ``await this.env.printer.printReceipt();`` (erstes BON)
  - ``await this.env.printer.printReceipt();`` (zweites BON direkt danach)

- Console-Warn bei Fehler

Warum ohne Delay:

- Moderne Printer können sequential queueing selbst
- Kein unnötiges Warten für User
- Sofortiger 2x BON-Druck
- Keine Race Conditions

4. Produktkarte flexible Höhe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Was: CSS-Anpassungen damit Produktkarten mit langen Namen nach unten mitwachsen.

Wie:

- ``.product-list``:

  - ``grid-template-columns: repeat(auto-fill, minmax(230px, 1fr))``

- ``.product-name``:

  - ``white-space: normal !important;``
  - ``text-overflow: clip !important;``
  - ``overflow: visible !important;``
  - ``display: block !important;``
  - ``-webkit-line-clamp: unset !important;``
  - ``line-height: 1.2 !important;``
  - ``height: auto !important;``
  - ``max-height: none !important;``

- ``.product-content``:

  - ``height: auto !important;``
  - ``min-height: 40% !important;``

- ``.product``:

  - ``height: auto !important;``
  - ``min-height: 180px !important;``

5. Limit für List Views
^^^^^^^^^^^^^^^^^^^^^^^

Was: Erweitert ``ir.actions.act_window`` um Standard-Limit.

Wie:

- Inherit ``ir.actions.act_window``
- Neues Feld ``limit`` (Integer)
- Default: ``200``
- Help: "Default limit for the list view"

Enthaltene Assets
-----------------

``pos_customization/_assets_pos``

POS-Assets (``point_of_sale._assets_pos``):

1. ``static/src/js/pos.js``

   - Patcht ``ControlButtons.prototype``
   - ``openDrawer()`` Methode für Cash Drawer

2. ``static/src/js/double_print.js``

   - Patcht ``PaymentScreen.prototype.validateOrder()``
   - Sofortiger 2x BON-Druck ohne Delay

3. ``static/src/xml/pos_button.xml``

   - Template ``pos_customization.ControlButtons``
   - Inherit ``point_of_sale.ControlButtons`` (extension mode)
   - Button "Kasse öffnen" mit ``t-on-click="openDrawer"``

4. ``static/src/xml/product_card.xml``

   - Template ``pos_customization.ProductCard``
   - Inherit ``point_of_sale.ProductCard`` (extension mode)
   - ``default_code`` Kopfzeile vor Produktbild (TASK ID: 51581)

5. ``static/src/css/pos_custom.css``

   - Flexible Produktkarten-Höhe
   - Mehrzeiliger Produktname
   - Grid-Layout Anpassungen

Models
------

``ir.actions.act_window``

Inherit: ``ir.actions.act_window``

Neues Feld:

- ``limit`` (Integer): Default limit für List Views

  - Default: ``200``
  - Help: "Default limit for the list view"

OWL Modules
-----------

``ControlButtons`` (``pos.js``)

Patched: ``ControlButtons.prototype`` from ``@point_of_sale/app/screens/product_screen/control_buttons/control_buttons``

Method:

- ``openDrawer()``: Öffnet Cash Drawer

  - Greift auf ``this.pos.hardwareProxy.printer.openCashbox()``
  - Fallback auf ``this.pos.hardwareProxy.openCashbox()``
  - Console.error bei Error

``PaymentScreen`` (``double_print.js``)

Patched: ``PaymentScreen.prototype`` from ``@point_of_sale/app/screens/payment_screen/payment_screen``

Method:

- ``validateOrder(isForceValidate)``: Override mit doppeltem Druck

  - ``await super.validateOrder(...arguments)``
  - ``await this.env.printer.printReceipt()`` (erstes BON)
  - ``await this.env.printer.printReceipt()`` (zweites BON direkt danach)
  - Console.warn bei Fehler

Templates
---------

``pos_customization.ControlButtons`` (``pos_button.xml``)

Inherit: ``point_of_sale.ControlButtons`` (extension mode)

XPath: ``//div[contains(@class, 'control-buttons-modal')]`` position="inside"

Button:

- Klasse: ``btn btn-secondary btn-lg py-5``
- Icon: ``<i class="fa fa-expand me-1" role="img" />``
- Text: "Kasse öffnen"
- Event: ``t-on-click="openDrawer"``

``pos_customization.ProductCard`` (``product_card.xml``)

Inherit: ``point_of_sale.ProductCard`` (extension mode)

XPath: ``//div[hasclass('product-img')]`` position="before"

Div:

- ``t-if="props.product.default_code"`` (bedingt)
- Klasse: ``w-100 px-2 py-1 text-muted fw-bold bg-light``
- Style: ``font-size: 0.85em; text-align: center; border-bottom: 1px solid #dee2e6; border-top-left-radius: 5px; border-top-right-radius: 5px;``
- Content: ``<t t-esc="props.product.default_code"/>``

Odoo 19 Kompatibilität
----------------------

OWL Module Syntax
^^^^^^^^^^^^^^^^^

- ``/** @odoo-module **/`` am Anfang
- ``import { patch } from "@web/core/utils/patch";``
- Keine ``this.`` in Event-Syntax: ``t-on-click="openDrawer"`` (nicht ``t-on-click="this.openDrawer"``)
- ``t-inherit-mode="extension"`` für OWL Templates

CSS Heben
^^^^^^^^^

- ``-webkit-line-clamp: unset !important;`` hebt Odoo 19 Text-Truncating auf
- ``white-space: normal !important;`` erlaubt Zeilenumbrüche
- ``overflow: visible !important;`` zeigt kompletten Text

Hardware Proxy
^^^^^^^^^^^^^^

- ``this.pos.hardwareProxy`` statt ``useService('hardware_proxy')``
- Direkt Zugriff auf ``printer.openCashbox()``

Installation
------------

1. Modul in den Addons-Pfad von Odoo legen
2. POS-Assets in Odoo aktualisieren (Cache clear)
3. Modul installieren
4. POS in Browser neu laden (F5 + Cache clear)

Hinweise
--------

- **Hardware Proxy erforderlich:** Cash Drawer funktioniert nur wenn Hardware Proxy konfiguriert ist
- **Doppelter BON sofort:** 2x Druck ohne unnötigen Delay, Printer queueing sequential
- **Artikelnummer oben:** Nur angezeigt wenn ``default_code`` vorhanden (``t-if``)
- **Flexible Höhe:** Produktkarten wachsen mit langen Namen nach unten
- **Limit Default:** List Views zeigen bis zu 200 Records ohne manuelle Limitierung
- **Task ID:** 51581 (Internal Reference auf Produktkarte)

Fehlerbehandlung
----------------

Cash Drawer
^^^^^^^^^^^

- Console.warn: "Hardware Proxy ist in der aktuellen POS-Sitzung nicht konfiguriert oder aktiv."
- Console.error: "Error while opening cash drawer: [error]"

Doppelter BON-Druck
^^^^^^^^^^^^^^^^^^^

- Console.warn: "[double_print] Druck fehlgeschlagen: [error]"
