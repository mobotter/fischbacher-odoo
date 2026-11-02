import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_sync_price_stock_to_woo(self):
        self.ensure_one()

        if not self.default_code:
            raise UserError(
                _("Das Produkt benötigt eine interne Referenz als WooCommerce-SKU.")
            )

        params = self.env["ir.config_parameter"].sudo()
        base_url = (params.get_param("fischbacher_woo.base_url") or "").rstrip("/")
        consumer_key = params.get_param("fischbacher_woo.consumer_key") or ""
        consumer_secret = params.get_param("fischbacher_woo.consumer_secret") or ""

        if not all([base_url, consumer_key, consumer_secret]):
            raise UserError(
                _(
                    "Bitte Shop-URL, Consumer Key und Consumer Secret "
                    "unter Einstellungen > Allgemeine Einstellungen > WooCommerce Sync hinterlegen."
                )
            )

        api_url = f"{base_url}/wp-json/wc/v3/products"

        auth_params = {
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
        }

        try:
            response = requests.get(
                api_url,
                params={
                    "sku": self.default_code,
                    **auth_params,
                },
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            _logger.exception("WooCommerce-Produktsuche fehlgeschlagen.")
            raise UserError(
                _("WooCommerce-Produktsuche fehlgeschlagen: %s") % error
            ) from error

        products = response.json()

        if len(products) != 1:
            raise UserError(
                _(
                    "Für die SKU '%(sku)s' wurden %(count)s WooCommerce-Produkte gefunden. "
                    "Es muss genau ein Produkt mit dieser SKU existieren."
                )
                % {
                    "sku": self.default_code,
                    "count": len(products),
                }
            )

        woo_product_id = products[0]["id"]

        quantity = max(0, int(self.qty_available))

        meta_data = [
            {
                "key": "_sale_price",
                "value": "",
            },
        ]

        if self.barcode:
            meta_data.extend([
                {
                    "key": "_global_unique_id",
                    "value": self.barcode,
                },
                {
                    "key": "_gm_gtin",
                    "value": self.barcode,
                },
            ])

        if quantity > 0:
            meta_data.append({
                "key": "_lieferzeit",
                "value": "43",
            })

        payload = {
            "regular_price": f"{self.list_price:.2f}",
            "sale_price": "",
            "manage_stock": True,
            "stock_quantity": quantity,
            "stock_status": "instock" if quantity > 0 else "outofstock",
            "meta_data": meta_data,
        }

        try:
            response = requests.put(
                f"{api_url}/{woo_product_id}",
                params=auth_params,
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            _logger.exception(
                "WooCommerce-Update für SKU %s fehlgeschlagen.",
                self.default_code,
            )
            raise UserError(
                _(
                    "Preis und Bestand konnten nicht nach WooCommerce übertragen werden: %s"
                )
                % error
            ) from error

        self.message_post(
            body=_(
                "WooCommerce-Sync erfolgreich: SKU %(sku)s, WooCommerce-ID %(woo_id)s, "
                "Nettopreis %(price)s, Bestand %(quantity)s."
            )
            % {
                "sku": self.default_code,
                "woo_id": woo_product_id,
                "price": f"{self.list_price:.2f}",
                "quantity": quantity,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("WooCommerce"),
                "message": _(
                    "Preis, Bestand und Zusatzfelder wurden für SKU %s synchronisiert."
                )
                % self.default_code,
                "type": "success",
                "sticky": False,
            },
        }
