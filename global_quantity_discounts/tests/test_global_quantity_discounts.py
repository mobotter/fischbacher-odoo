# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGlobalQuantityDiscounts(TransactionCase):
    """Preisfindung für KLEBEBAND (Listenpreis 4,50 EUR).

    * Mengenstaffeln (global): 25 % ab 60 Stück (Produktregel),
      30 % ab 500 Stück (Kategorieregel)
    * Default (global):        Festpreis 3,20 ab 100 Stück (Produktregel)
    * Kunde 10 %:              10 % auf alles
    * Kunde Festpreis:         Festpreis 3,80 (Produktregel), sonst 10 %
    * Andere Kunden-PL:        nicht global, kundenspezifische Preise
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("product.decimal_price").digits = 3

        cls.currency = cls.env.company.currency_id
        cls.Pricelist = cls.env["product.pricelist"]

        # Vorhandene Preislisten (Demo-/Kundendaten) neutralisieren.
        cls.Pricelist.with_context(active_test=False).search(
            [("is_global_quantity_pricelist", "=", True)]
        ).is_global_quantity_pricelist = False

        cls.category = cls.env["product.category"].create({"name": "Klebebänder"})
        cls.product = cls.env["product.product"].create({
            "name": "KLEBEBAND 55cmx18m",
            "list_price": 4.50,
            "categ_id": cls.category.id,
            "taxes_id": [Command.clear()],
        })
        tmpl = cls.product.product_tmpl_id

        cls.staffel = cls.Pricelist.create({
            "name": "Mengenstaffeln (Test)",
            "currency_id": cls.currency.id,
            "is_global_quantity_pricelist": True,
            "item_ids": [
                Command.create({
                    "applied_on": "1_product",
                    "product_tmpl_id": tmpl.id,
                    "compute_price": "percentage",
                    "percent_price": 25.0,
                    "min_quantity": 60,
                }),
                Command.create({
                    "applied_on": "2_product_category",
                    "categ_id": cls.category.id,
                    "compute_price": "percentage",
                    "percent_price": 30.0,
                    "min_quantity": 500,
                }),
            ],
        })

        cls.default_pricelist = cls.Pricelist.create({
            "name": "Default (Test)",
            "currency_id": cls.currency.id,
            "is_global_quantity_pricelist": True,
            "item_ids": [Command.create({
                "applied_on": "1_product",
                "product_tmpl_id": tmpl.id,
                "compute_price": "fixed",
                "fixed_price": 3.20,
                "min_quantity": 100,
            })],
        })

        cls.pricelist_percent = cls.Pricelist.create({
            "name": "Kunde 10 %",
            "currency_id": cls.currency.id,
            "item_ids": [Command.create({
                "applied_on": "3_global",
                "compute_price": "percentage",
                "percent_price": 10.0,
            })],
        })

        cls.pricelist_fixed = cls.Pricelist.create({
            "name": "Kunde Festpreis",
            "currency_id": cls.currency.id,
            "item_ids": [
                Command.create({
                    "applied_on": "1_product",
                    "product_tmpl_id": tmpl.id,
                    "compute_price": "fixed",
                    "fixed_price": 3.80,
                }),
                Command.create({
                    "applied_on": "3_global",
                    "compute_price": "percentage",
                    "percent_price": 10.0,
                }),
            ],
        })

        cls.other_pricelist = cls.Pricelist.create({
            "name": "Anderer Kunde",
            "currency_id": cls.currency.id,
        })

        cls.partner = cls.env["res.partner"].create({"name": "Testkunde"})

    # ------------------------------------------------------------------

    def _pricelist_price(self, pricelist, qty):
        return pricelist._get_product_price(self.product, qty, currency=self.currency)

    def _order(self, pricelist, *quantities):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "pricelist_id": pricelist.id,
            "order_line": [
                Command.create({"product_id": self.product.id, "product_uom_qty": qty})
                for qty in quantities
            ],
        })

    def _order_line_price(self, pricelist, qty):
        """Effektiver Preis einer Angebotszeile (price_unit abzgl. Rabatt)."""
        line = self._order(pricelist, qty).order_line
        return line.price_unit * (1 - line.discount / 100.0)

    def _assert_price(self, pricelist, qty, expected):
        self.assertAlmostEqual(self._pricelist_price(pricelist, qty), expected, places=3)
        self.assertAlmostEqual(self._order_line_price(pricelist, qty), expected, places=3)

    # --- Szenarien aus der README --------------------------------------

    def test_scenario_1_discount_allowed(self):
        self.product.discount_allowed = True
        self._assert_price(self.pricelist_percent, 50, 4.05)
        self._assert_price(self.pricelist_percent, 70, 3.375)

    def test_scenario_2_discount_not_allowed(self):
        """Keine Rabatte: weder Kundenrabatt noch prozentuale Staffel."""
        self.product.discount_allowed = False
        self._assert_price(self.pricelist_percent, 50, 4.50)
        self._assert_price(self.pricelist_percent, 70, 4.50)

    def test_scenario_3_fixed_price_not_allowed(self):
        self.product.discount_allowed = False
        self._assert_price(self.pricelist_fixed, 50, 3.80)
        self._assert_price(self.pricelist_fixed, 70, 3.80)

    # --- Staffelpreise aus dem Produkt-Reiter "Preise" -----------------

    def test_product_tab_fixed_staffel_default(self):
        for allowed in (True, False):
            self.product.discount_allowed = allowed
            self._assert_price(self.pricelist_percent, 120, 3.20)
            self._assert_price(self.pricelist_fixed, 120, 3.20)

    def test_customer_specific_prices_stay_customer_specific(self):
        """Produktregeln einer Kundenpreisliste gelten nur für diese."""
        self.other_pricelist.item_ids = [
            Command.create({
                "applied_on": "1_product",
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "compute_price": "fixed",
                "fixed_price": 0.0,
            }),
        ]
        self.product.discount_allowed = False
        self._assert_price(self.pricelist_percent, 1, 4.50)
        self._assert_price(self.pricelist_fixed, 1, 3.80)
        self._assert_price(self.other_pricelist, 1, 0.0)

    def test_customer_pricelist_competes_with_global(self):
        """Kundenpreis 3,00 ab 200 schlägt Default 3,20, nur für diesen Kunden."""
        self.other_pricelist.item_ids = [Command.create({
            "applied_on": "1_product",
            "product_tmpl_id": self.product.product_tmpl_id.id,
            "compute_price": "fixed",
            "fixed_price": 3.00,
            "min_quantity": 200,
        })]
        self.product.discount_allowed = False
        self._assert_price(self.other_pricelist, 150, 3.20)
        self._assert_price(self.other_pricelist, 250, 3.00)
        self._assert_price(self.pricelist_percent, 250, 3.20)

    def test_global_percentage_respects_discount_allowed(self):
        self.default_pricelist.item_ids = [Command.create({
            "applied_on": "0_product_variant",
            "product_id": self.product.id,
            "compute_price": "percentage",
            "percent_price": 40.0,
        })]
        self.product.discount_allowed = True
        self._assert_price(self.pricelist_percent, 1, 2.70)
        self.product.discount_allowed = False
        self._assert_price(self.pricelist_percent, 1, 4.50)

    def test_category_rule_of_other_pricelist_ignored(self):
        """Kategorie-/globale Regeln nicht markierter Preislisten zählen nicht."""
        self.other_pricelist.item_ids = [Command.create({
            "applied_on": "2_product_category",
            "categ_id": self.category.id,
            "compute_price": "fixed",
            "fixed_price": 1.00,
        })]
        self._assert_price(self.pricelist_percent, 1, 4.05)

    def test_category_rule_of_global_pricelist(self):
        """Kategorieregeln gelten nur aus global markierten Preislisten."""
        product2 = self.env["product.product"].create({
            "name": "KLEBEBAND schmal",
            "list_price": 4.50,
            "categ_id": self.category.id,
            "taxes_id": [Command.clear()],
        })

        def price(qty):
            return self.pricelist_percent._get_product_price(
                product2, qty, currency=self.currency
            )

        self.assertAlmostEqual(price(500), 3.15, places=3)
        self.staffel.is_global_quantity_pricelist = False
        self.assertAlmostEqual(price(500), 4.05, places=3)

    # --- Sonstiges -----------------------------------------------------

    def test_no_stacking(self):
        """Staffel rechnet vom Listenpreis, nicht vom Kundenpreis."""
        self.product.discount_allowed = True
        self.assertAlmostEqual(self._pricelist_price(self.pricelist_percent, 70), 3.375)

    def test_variant_uses_template_value(self):
        self.product.product_tmpl_id.discount_allowed = False
        self.assertFalse(self.product.discount_allowed)

    def test_staffel_pricelist_itself(self):
        self.product.discount_allowed = True
        self._assert_price(self.staffel, 70, 3.375)
        self._assert_price(self.staffel, 50, 4.50)

    def test_line_discount_display(self):
        """Mit 'Rabatte auf Positionen': Rabatt als Prozent in der Zeile,
        bei nicht rabattfähigen Produkten nie."""
        self.env.ref("base.group_user").implied_ids |= self.env.ref(
            "sale.group_discount_per_so_line"
        )
        self.env.invalidate_all()

        self.product.discount_allowed = True
        line_70, line_50 = self._order(self.pricelist_percent, 70, 50).order_line
        self.assertAlmostEqual(line_70.price_unit, 4.50, places=3)
        self.assertAlmostEqual(line_70.discount, 25.0, places=2)
        self.assertAlmostEqual(line_50.discount, 10.0, places=2)

        self.product.discount_allowed = False
        line_70, line_50 = self._order(self.pricelist_percent, 70, 50).order_line
        for line in (line_70, line_50):
            self.assertAlmostEqual(line.price_unit, 4.50, places=3)
            self.assertEqual(line.discount, 0.0)

    def test_offer_fixed_price_beats_everything(self):
        """Festpreis aus einem gültigen Kundenangebot gilt immer
        (nur mit sale_customer_offer_price)."""
        if "fixed_price" not in self.env["sale.order.line"]._fields:
            self.skipTest("sale_customer_offer_price nicht installiert")

        self.product.discount_allowed = True
        self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "pricelist_id": self.pricelist_percent.id,
            "order_line": [Command.create({
                "product_id": self.product.id,
                "price_unit": 3.90,
            })],
        })
        order = self._order(self.pricelist_percent, 1)
        line = order.order_line
        self.assertAlmostEqual(line.price_unit * (1 - line.discount / 100), 4.05, places=3)

        action = line.action_save_and_open_wizard()
        self.env[action["res_model"]].browse(action["res_id"]).action_accept()
        self.assertAlmostEqual(line.price_unit, 3.90, places=3)

        for qty in (70, 120, 500):
            line.product_uom_qty = qty
            self.assertAlmostEqual(line.price_unit, 3.90, places=3)
            self.assertEqual(line.discount, 0.0)

        order.action_update_prices()
        self.assertAlmostEqual(line.price_unit, 3.90, places=3)
