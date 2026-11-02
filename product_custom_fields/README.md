Adds Custom Fields to Products
==============================

Autor: Moritz Kern
Firma: Fischbacher GmbH + Co. KG

Übersicht
=========

Dieses Modul erweitert Odoo-Produkte (``product.product``) und
Produktkategorien (``product.category``) um projektspezifische Felder und
Validierungen. Es unterstützt insbesondere:

- Pflicht-Stammdaten: Produktname, Artikelnummer, Barcode und Verkaufspreis
- Suche und Identifikation: Suchbegriff, Kurzname, Herstellernummer und DSP3-ID
- Vermietung: Prüfdaten für TÜV, UVV und Bremsen
- Webshop: Webshop-Link, externe IDs und nicht-variantierende Website-Attribute
- Lieferanten: Hauptlieferant und Lieferanten-Produktnummer
- Kategorien: Kategorie-Nummer für vollständige Namensbildung
- Boni und Sonderverkäufe: Bonus- und Sonderverkauf-Flags

Technische Details
==================

- Technischer Name: ``product_custom_fields``
- Name: ``Adds Custom Fields to Products``
- Autor: ``Moritz Kern, Odolution``
- Version: ``19.0.1.1.0``
- Lizenz: ``LGPL-3``
- Abhängigkeiten: ``sale``, ``website_sale``
- Installierbar: ``True``
- Auto Install: ``False``

Pflichtangaben bei Produkten
=============================

Beim Anlegen und Speichern eines Produkts sind folgende Daten verpflichtend:

- Produktname (``name``)
- Artikelnummer / interne Referenz (``default_code``)
- Barcode (``barcode``)
- Verkaufspreis größer als ``0,00 €`` (``list_price``)

Im Produktformular wird oben folgender Warnhinweis angezeigt:

    Bitte Produktname, Artikelnummer, Barcode und Preis eintragen!

Validierungsverhalten
=====================

Die Prüfung erfolgt auf zwei Ebenen.

Formularansicht
---------------

- Die vier Angaben sind als Pflichtfelder markiert.
- Der Nutzer erhält den sichtbaren Warnhinweis im Produktformular.

Serverseitige Prüfung
---------------------

- Das Speichern wird bei fehlenden Angaben oder einem Preis von ``0,00 €``
  beziehungsweise weniger blockiert.
- Die Prüfung greift auch bei CSV-/XLSX-Importen, XML-RPC/JSON-RPC,
  API-Aufrufen, Connectoren, automatisierten Aktionen und sonstigen
  Hintergrundprozessen.
- Beim Öffnen eines neuen Produktformulars erfolgt keine serverseitige
  Pflichtdatenvalidierung, damit die leere Eingabemaske geöffnet werden kann.

Preis-Default
=============

Ein möglicherweise durch eine Fremdanpassung gesetzter Default von ``1,00 €``
wird beim Anlegen eines Produkts auf ``0,00 €`` zurückgesetzt. Dadurch kann
kein Produkt versehentlich mit diesem Standardwert gespeichert werden.

``list_price`` ist ein Float-Feld. Ein nicht eingegebener Preis wird technisch
als ``0.0`` geführt; deshalb prüft das Modul ausdrücklich, ob der
Verkaufspreis größer als ``0.0`` ist.

Erweiterte Modelle
==================

product.product
---------------

Erweitert das Produktmodell um folgende Felder und Funktionen.

Pflicht-Stammdaten
~~~~~~~~~~~~~~~~~~

- ``name`` (Char): Produktname; beim Speichern erforderlich
- ``default_code`` (Char): Artikelnummer / interne Referenz; beim Speichern erforderlich
- ``barcode`` (Char): Barcode; beim Speichern erforderlich
- ``list_price`` (Float): Verkaufspreis; muss größer als ``0,00 €`` sein

Suche und Identifikation
~~~~~~~~~~~~~~~~~~~~~~~~

- ``search_term`` (Char): Suchbegriff für erweiterte Produktsuche
- ``short_term`` (Char): Kurzname des Produkts
- ``manufacturer_number`` (Char): Herstellernummer
- ``dsp3_id`` (Char): DSP3-ID

Vermietung
~~~~~~~~~~

- ``is_rental_available`` (Boolean): Ist für Vermietung verfügbar
- ``inspection_date`` (Date): Prüfdatum / TÜV
- ``uvv_date`` (Date): UVV-Prüfdatum
- ``brake_inspection_date`` (Date): Bremsen-Prüfdatum

Lieferanten
~~~~~~~~~~~

- ``main_supplier_id`` (Many2one zu ``product.supplierinfo``): Hauptlieferant;
  automatisch aus dem ersten Lieferantendatensatz berechnet
- ``main_supplier_product_number`` (Char): Lieferanten-Produktnummer;
  automatisch berechnet

Webshop und externe IDs
~~~~~~~~~~~~~~~~~~~~~~~

- ``webshop_link`` (Char): Webshop-Link; mit URL-Widget dargestellt
- ``external_id`` (Integer): Externe ID
- ``brand_id`` (Many2one zu ``product.brand``): Marke

Dimensionen
~~~~~~~~~~~

- ``length`` (Char): Länge
- ``width`` (Char): Breite
- ``height`` (Char): Höhe

Website-Attribute
~~~~~~~~~~~~~~~~~

- ``product_website_product_attribute_ids`` (One2many zu
  ``product.website.attribute.product``): Website-Attributwerte für das Produkt
- ``product_website_attribute_ids`` (Many2many zu
  ``product.website.attribute``): Website-Attribute

Boni und Sonderverkäufe
~~~~~~~~~~~~~~~~~~~~~~~

- ``bonus_applicable`` (Boolean): Bonus anwendbar
- ``special_sale_applicable`` (Boolean): Sonderverkauf anwendbar

product.category
----------------

Erweitert Produktkategorien um:

- ``category_number`` (Char): Kategorie-Nummer
- ``complete_name`` (Char, berechnet): Vollständiger Name mit Kategorie-Nummer

Berechnung von ``complete_name``:

- Mit übergeordneter Kategorie: ``Parent / [Kategorie-Nummer] Name``
- Ohne übergeordnete Kategorie: ``[Kategorie-Nummer] Name``

Neue Modelle
============

product.brand
-------------

Eigenes Modell für Produktmarken:

- ``name`` (Char): Markenname; auch ``_rec_name``
- ``image`` (Image): Markenbild
- ``external_id`` (Integer): Externe ID

product.website.attribute
-------------------------

Modell für nicht-variantierende Website-Attribute. Diese Attribute erzeugen
keine Produktvarianten.

- ``name`` (Char): Attributname; auch ``_rec_name``
- ``external_id`` (Integer): Externe ID
- ``sequence`` (Integer): Reihenfolge
- ``visible`` (Boolean): Sichtbar
- ``option_ids`` (One2many zu ``product.website.attribute.value``):
  Attributoptionen

product.website.attribute.value
-------------------------------

Modell für Optionen von Website-Attributen:

- ``name`` (Char): Optionsname; auch ``_rec_name``
- ``external_id`` (Integer): Externe ID
- ``attribute_id`` (Many2one zu ``product.website.attribute``):
  Zugehöriges Attribut

product.website.attribute.product
---------------------------------

Verknüpfung zwischen Produkten und Website-Attributen:

- ``product_id`` (Many2one zu ``product.product``): Produkt
- ``attribute_id`` (Many2one zu ``product.website.attribute``): Attribut
- ``value_ids`` (Many2many zu ``product.website.attribute.value``):
  Ausgewählte Werte

product.supplierinfo
--------------------

Die Felder ``main_supplier_id`` und ``main_supplier_product_number`` auf
``product.product`` werden aus dem ersten Lieferantendatensatz
(``seller_ids[0]``) berechnet.

Enthaltene Views
================

views/product_form.xml
----------------------

View: ``product_form_view_inherit``

Erweitert die normale Produktformularansicht
(``product.product_normal_form_view``) um:

- Gelben Warnhinweis: „Bitte Produktname, Artikelnummer, Barcode und Preis eintragen!“
- Pflicht-Markierung für ``name``, ``default_code``, ``barcode`` und ``list_price``
- ``search_term`` und ``short_term`` nach ``categ_id``
- ``dsp3_id`` nach ``default_code``
- ``bonus_applicable``, ``special_sale_applicable``, ``manufacturer_number``,
  ``main_supplier_id`` und ``main_supplier_product_number`` nach
  ``product_tooltip``
- Zusätzliche Notebook-Seite Product Data mit:

  - Gruppe Base Data: ``brand_id``, ``width``, ``length``, ``height``, ``weight``
  - Gruppe Rent Data: ``inspection_date``, ``uvv_date``, ``brake_inspection_date``
  - Gruppe Website Data: ``webshop_link``, ``external_id``,
    ``product_website_product_attribute_ids``

views/product_search.xml
------------------------

Vier Erweiterungen der Produktsuche:

1. ``product_search_form_view_inherited_name``: Produktsuche nach
   ``default_code``, ``name``, ``barcode``, ``search_term`` und ``short_term``
2. ``product_search_form_view_inherited_shortterm``: Suche nach Kurzname
   (``short_term``)
3. ``product_search_form_view_inherited_searchterm``: Suche nach Suchbegriff
   (``search_term``)
4. ``product_search_form_view_inherited_manufacturer``: Suche nach
   Herstellernummer (``manufacturer_number``)

views/category.xml
------------------

View: ``product_category_form_view_inherit``

Erweitert die Kategorieansicht um ``category_number`` nach ``parent_id``.

views/product_attribute.xml
---------------------------

Enthält die Ansichten für Website-Attribute:

- ``product_website_attribute_view_form``: Formularansicht für Website-Attribute
- ``product_website_attribute_view_tree``: Listenansicht für Website-Attribute;
  bearbeitbar am Listenende und mit Reihenfolge-Handle
- ``product_website_attribute_value_view_tree``: Listenansicht für
  Website-Attributwerte; bearbeitbar am Listenende

views/menu.xml
--------------

Menüpunkte unter Produktkonfiguration (``sale.prod_config_main``):

- ``menu_website_attribute_config``: Website Attributes → ``website_attribute_action``
- ``menu_website_attribute_value_config``: Website Attribute Values →
  ``website_attribute_value_action``

Security
========

security/groups.xml
-------------------

Definiert Benutzergruppen für die neuen Modelle:

- ``product_brand_user``: Product Brand User
- ``product_website_attribute_user``: Website Attribute User
- ``product_website_attribute_value_user``: Website Attribute Value User
- ``product_website_attribute_product_user``: Website Attribute Product User

security/ir.model.access.csv
-----------------------------

Definiert Vollzugriff (Lesen, Schreiben, Anlegen, Löschen) für:

- ``product.brand``
- ``product.website.attribute``
- ``product.website.attribute.value``
- ``product.website.attribute.product``

Methoden
========

product.product.create()
------------------------

Ergänzt die Produkterstellung wie folgt:

- Ein übergebener Preis-Default von exakt ``1.0`` wird auf ``0.0`` zurückgesetzt.
- Es erfolgt bewusst keine Pflichtdatenprüfung innerhalb von ``create()``, da
  Odoo beim Klick auf „Neu“ bereits einen unvollständigen technischen
  Produktdatensatz beziehungsweise eine Standardvariante anlegen kann.

product.product.write()
-----------------------

Prüft bei Änderungen an ``name``, ``default_code``, ``barcode`` oder
``list_price`` die Pflicht-Stammdaten. So kann kein Produkt durch eine
Bearbeitung in einen unzulässigen Zustand gebracht werden.

product.product._check_required_product_data()
----------------------------------------------

Prüft pro Produkt:

- Produktname vorhanden
- Artikelnummer vorhanden
- Barcode vorhanden
- Verkaufspreis größer als ``0.0``

Fehlende oder ungültige Angaben führen zu einer ``ValidationError``-Meldung
mit einer Auflistung der betroffenen Felder.

product.product._compute_supplier()
------------------------------------

Abhängigkeiten: ``seller_ids``, ``seller_ids.product_code``,
``seller_ids.partner_id``, ``seller_ids.price``

Berechnet automatisch:

- ``main_supplier_id`` = ``seller_ids[0].partner_id``
- ``main_supplier_product_number`` = ``seller_ids[0].product_code``

product.product.name_search()
-----------------------------

Erweiterte Suche nach:

- ``name``
- ``default_code``
- ``description_sale``
- ``search_term``
- ``short_term``

product.category._compute_complete_name()
-----------------------------------------

Abhängigkeiten: ``name``, ``parent_id.complete_name``

Berechnet ``complete_name`` einschließlich Kategorie-Nummer.

Odoo-19-Status
==============

Das Modul ist für Odoo 19 ausgelegt:

- Version ``19.0.1.1.0`` im Manifest
- ``installable: True`` im Manifest
- ``auto_install: False`` im Manifest
- Produkt-Pflichtdaten im Formular und serverseitig bei relevanten Änderungen validiert
- ``_rec_name = 'name'`` für die neuen Stammdatenmodelle
- Korrigierte, eindeutige View- und Action-IDs
- Getrennte Records für die erweiterten Search Views
- Benutzergruppen in ``security/groups.xml``

Installation und Upgrade
========================

1. Den Modulordner ``product_custom_fields`` in einen konfigurierten
   Odoo-Addons-Pfad legen.
2. Den Odoo-Dienst neu starten.
3. Entwicklermodus aktivieren.
4. In Apps die App-Liste aktualisieren.
5. Das Modul installieren oder die bestehende Installation upgraden.

Beispiel für ein Upgrade über die Kommandozeile::

    ./odoo-bin -d DEINE_DATENBANK -u product_custom_fields --stop-after-init

Danach Odoo normal starten. Bei einer systemd-Installation beispielsweise::

    sudo systemctl restart odoo

Hinweise
========

- Das Modul ist primär für Vermietungs-Baumaschinen konzipiert.
- Website-Attribute sind nicht variantenerzeugend.
- Der Hauptlieferant wird aus dem ersten Lieferanten in ``seller_ids`` ermittelt.
- Die Kategorie-Nummer verbessert die Lesbarkeit vollständiger Kategorienamen.
- ``webshop_link`` verwendet das Odoo-URL-Widget.
- Die Pflichtprüfung wurde auf ``product.product`` implementiert, da das Modul
  und die vorhandene Formularansicht auf Variantenebene arbeiten.
- Bei Produkten mit mehreren Varianten kann es sinnvoll sein, eine zusätzliche
  Prüfung auf ``product.template`` umzusetzen, wenn Produktnamen oder
  Verkaufspreise bereits bei der Template-Anlage verbindlich sein sollen.
