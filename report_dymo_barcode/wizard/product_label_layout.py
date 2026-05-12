from odoo import _, api, fields, models
from odoo.exceptions import UserError
import requests
import base64
import logging

_logger = logging.getLogger(__name__)

class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    # Neues Feld für das Vorschaubild
    zpl_preview_image = fields.Binary(string="ZPL Vorschau", readonly=True)

    print_format = fields.Selection(
        selection_add=[
            ('sep_dymo', '--- PDF / DYMO ETIKETTEN ---'),  # Visuelle Trennung
            ('dymo_price', 'FB Dymo Price (89x36mm)'),
            ('dymo_without_price', 'FB Dymo without Price (89x36mm)'),
            ('dymo_artikel_barcode', 'FB Dymo Artikel Barcode (89x36mm)'),
            ('dymo_small', 'FB Dymo Small (54x25mm)'),
            ('dymo_price_small', 'FB Dymo Price Small (54x25mm)'),
            ('sep_zpl', '--- ZPL / ZEBRA ETIKETTEN---'),     # Visuelle Trennung
            ('zpl_small', 'FB ZPL Zebra small label'),
            ('zpl_without_price', 'FB ZPL Zebra without Price')
        ], 
        ondelete={
            'sep_dymo': 'set default',
            'dymo_price': 'set default',
            'dymo_without_price': 'set default',
            'dymo_artikel_barcode': 'set default',
            'dymo_price_small': 'set default',
            'dymo_small': 'set default',
            'sep_zpl': 'set default',
            'zpl_small': 'set default',
            'zpl_without_price': 'set default'
        }
    )

    def _prepare_report_data(self):
        # 1. SICHERHEITSPRÜFUNG HINZUFÜGEN
        if self.print_format in ['sep_dymo', 'sep_zpl']:
            raise UserError(_("Bitte wählen Sie ein konkretes Etikettenformat aus, keine Überschrift."))

        xml_id, data = super()._prepare_report_data()
        
        # 2. IHR BESTEHENDES MAPPING
        report_mapping = {
            'dymo_price': 'report_dymo_barcode.report_product_template_label_dymo_price',
            'dymo_without_price': 'report_dymo_barcode.report_product_template_label_dymo_without_price',
            'dymo_artikel_barcode': 'report_dymo_barcode.report_product_template_label_dymo_artikel_barcode',
            'dymo_price_small': 'report_dymo_barcode.report_product_template_label_dymo_price_small',
            'dymo_small': 'report_dymo_barcode.report_product_template_label_dymo_small',
            'zpl_small': 'report_dymo_barcode.report_product_template_label_zpl_small',
            'zpl_without_price': 'report_dymo_barcode.report_product_template_label_zpl_without_price'
        }
        
        if self.print_format in report_mapping:
            xml_id = report_mapping[self.print_format]
            
        return xml_id, data

    def action_generate_zpl_preview(self):
        self.ensure_one()
        
        # Nur für ZPL-Formate ausführen
        if self.print_format not in ['zpl_small', 'zpl_without_price']:
            raise UserError(_("Eine Vorschau kann nur für ZPL-Etiketten generiert werden."))
            
        # Holen Sie sich die richtige Report-ID anhand der aktuellen Auswahl
        xml_id, _data = self._prepare_report_data()
        report = self.env.ref(xml_id)
        
        record_ids = self.product_tmpl_ids.ids if self.product_tmpl_ids else self.product_ids.ids
        
        if not record_ids:
            return
            
        try:
            # 1. ZPL-Code für das erste Produkt rendern
            zpl_content, _ = report._render_qweb_text([record_ids[0]])
            zpl_string = zpl_content.decode('utf-8')

            # 2. API Call zu Labelary
            # Wir nutzen standardmäßig 8dpmm (203dpi) und 80x30mm (ca 3.15x1.18 Inch)
            url = 'http://api.labelary.com/v1/printers/8dpmm/labels/3.15x1.18/0/'
            headers = {'Accept': 'image/png'}
            response = requests.post(url, headers=headers, data=zpl_string.encode('utf-8'), timeout=5)
            
            # 3. Bild speichern
            if response.status_code == 200:
                self.zpl_preview_image = base64.b64encode(response.content)
            else:
                _logger.warning("Labelary API Fehler: %s", response.status_code)
                raise UserError(_("Fehler bei der Verbindung zu Labelary. (Status: %s)") % response.status_code)
                
        except Exception as e:
            _logger.error("Fehler bei der ZPL-Vorschau Generierung: %s", str(e))
            raise UserError(_("Die Vorschau konnte nicht generiert werden: %s") % str(e))
        
        # Fenster (Wizard) nach Button-Klick offen halten
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
