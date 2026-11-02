from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date


DONE_STATES = ("done",)
OPEN_STATES = ("waiting", "confirmed", "assigned", "partially_available")
DROPSHIP_STATES = (
    "done",
    "assigned",
    "confirmed",
    "waiting",
    "partially_available",
)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_door = fields.Text(string="Bestellt durch")
    print_delivery_address = fields.Boolean(
        string="Lieferadresse drucken",
        default=False,
    )
    purchase_no_backup = fields.Char(string="Purchase")
    order_number_backup = fields.Char(string="Order Number")
    is_rent_backup = fields.Boolean(string="Rent")
    hide_total_backup = fields.Boolean(string="Hide Total Amount")
    german_payment_term_backup = fields.Char(string="Zahlungsbedingungen")

    client_order_name = fields.Char(string="Bestellt durch")
    client_order_number = fields.Char(string="Ihre Bestellnummer")
    client_order_ref = fields.Text(string="Projekt / Kundenreferenz")

    def action_print_combined_delivery_slip(self):
        """Erzeugt den kombinierten Lieferschein als PDF."""
        report = self.env.ref(
            "ol_delivery_slip_changes.action_report_combined_delivery",
            raise_if_not_found=False,
        )

        if not report:
            raise UserError(
                _(
                    "Die Report-Aktion für den kombinierten Lieferschein wurde "
                    "nicht gefunden. Bitte aktualisieren Sie das Modul "
                    "„ol_delivery_slip_changes“."
                )
            )

        return report.with_context(
            print_date=format_date(self.env, datetime.now().date())
        ).report_action(self)

    def _get_outgoing_pickings(self, states):
        """Liefert Ausgangslieferungen des Auftrags in den gewünschten Stati."""
        self.ensure_one()

        return self.picking_ids.filtered(
            lambda picking: (
                picking.picking_type_code == "outgoing"
                and picking.state in states
            )
        ).sorted(
            key=lambda picking: (
                picking.date_done
                or picking.scheduled_date
                or picking.create_date
            )
        )

    def _get_dropship_pickings(self, states):
        """Liefert Streckengeschäftslieferungen des Auftrags in den gewünschten Stati."""
        self.ensure_one()

        return self.picking_ids.filtered(
            lambda picking: (
                picking.picking_type_code == "dropship"
                and picking.state in states
            )
        ).sorted(
            key=lambda picking: (
                picking.date_done
                or picking.scheduled_date
                or picking.create_date
            )
        )

    def get_done_pickings(self):
        """Alle abgeschlossenen Lagerausgangslieferungen."""
        self.ensure_one()
        return self._get_outgoing_pickings(DONE_STATES)

    def get_open_pickings(self):
        """Alle offenen bzw. geplanten Lagerausgangslieferungen."""
        self.ensure_one()
        return self._get_outgoing_pickings(OPEN_STATES)

    def get_dropship_pickings(self):
        """Alle relevanten Streckengeschäftslieferungen."""
        self.ensure_one()
        return self._get_dropship_pickings(DROPSHIP_STATES)

    def get_done_move_lines(self):
        """Aggregiert erledigte Positionen aus allen abgeschlossenen Lagerlieferungen."""
        self.ensure_one()
        return self._aggregate_moves(
            self.get_done_pickings(),
            use_done=True,
        )

    def get_open_move_lines(self):
        """Aggregiert offene Positionen aus allen offenen Lagerlieferungen."""
        self.ensure_one()
        return self._aggregate_moves(
            self.get_open_pickings(),
            use_done=False,
        )

    def get_dropship_move_lines(self):
        """Aggregiert Positionen aus Streckengeschäftslieferungen."""
        self.ensure_one()
        return self._aggregate_moves(
            self.get_dropship_pickings(),
            use_done=True,
        )

    def _aggregate_moves(self, pickings, use_done=True):
        """
        Führt Stock Moves desselben Produkts und derselben Einheit zusammen.

        Die Schlüsselung erfolgt über Produkt und Einheit. Dadurch werden
        unterschiedliche UoMs für dieselbe Produktvariante nicht unbemerkt
        addiert, etwa Stück und Meter.

        Rückgabe:
        [
            {
                "product": product.product(...),
                "product_uom_qty": 2.0,
                "qty_done": 1.0,
                "uom_name": "Stk",
                "lot_names": ["LOT-001"],
                "picking_names": ["WH/OUT/00001"],
                "is_dropship": False,
            },
        ]
        """
        self.ensure_one()

        line_map = {}

        for picking in pickings:
            relevant_moves = picking.move_ids.filtered(
                lambda move: (
                    move.state == "done"
                    if use_done
                    else move.state not in ("cancel", "done")
                )
            )

            for move in relevant_moves:
                if not move.product_id:
                    continue

                product = move.product_id
                uom = move.product_uom or product.uom_id
                key = (product.id, uom.id)

                if key not in line_map:
                    line_map[key] = {
                        "product": product,
                        "product_uom_qty": 0.0,
                        "qty_done": 0.0,
                        "uom_name": uom.name,
                        "lot_names": [],
                        "picking_names": [],
                        "is_dropship": (
                            picking.picking_type_code == "dropship"
                        ),
                    }

                result_line = line_map[key]

                if (
                    picking.name
                    and picking.name not in result_line["picking_names"]
                ):
                    result_line["picking_names"].append(picking.name)

                result_line["product_uom_qty"] += (
                    move.product_uom_qty or 0.0
                )

                if use_done:
                    result_line["qty_done"] += move.quantity or 0.0

                    for move_line in move.move_line_ids:
                        lot_name = (
                            move_line.lot_id.name
                            if move_line.lot_id
                            else False
                        )

                        if (
                            lot_name
                            and lot_name not in result_line["lot_names"]
                        ):
                            result_line["lot_names"].append(lot_name)

        return list(line_map.values())

    def get_service_lines(self):
        """Ermittelt alle echten Dienstleistungspositionen des Auftrags."""
        self.ensure_one()

        services = []

        for line in self.order_line.filtered(
            lambda line: (
                not line.display_type
                and line.product_id
                and line.product_id.type == "service"
            )
        ):
            ordered_qty = line.product_uom_qty or 0.0
            delivered_qty = line.qty_delivered or 0.0

            if delivered_qty >= ordered_qty:
                status = _("Erledigt")
                status_class = "success"
            elif delivered_qty > 0:
                status = _("Teilweise erledigt")
                status_class = "warning"
            else:
                status = _("Offen")
                status_class = "secondary"

            services.append({
                "line": line,
                "status": status,
                "status_class": status_class,
            })

        return services

    def get_all_order_lines_with_status(self):
        """
        Erstellt die Positionen des kombinierten Lieferscheins.

        Berücksichtigt:
        - erledigte Lagerausgangslieferungen,
        - offene Lagerausgangslieferungen,
        - Streckengeschäftslieferungen,
        - Dienstleistungen aus den Auftragspositionen,
        - physische Auftragspositionen ohne Picking als Fallback.

        Diese Methode wird im QWeb-Report je sale.order aufgerufen und
        arbeitet daher bewusst auf genau einem Auftrag.
        """
        self.ensure_one()

        all_lines = []
        covered_product_ids = set()

        # 1. Erledigte Lagerpositionen
        for line in self.get_done_move_lines():
            product = line["product"]
            covered_product_ids.add(product.id)

            all_lines.append({
                "product": product,
                "product_uom_qty": line["product_uom_qty"],
                "qty_done": line["qty_done"],
                "uom_name": line["uom_name"],
                "lot_names": line["lot_names"],
                "picking_names": line["picking_names"],
                "status": _("Erledigt"),
                "status_class": "success",
                "line_type": _("Lager"),
                "is_dropship": False,
                "comment": False,
            })

        # 2. Offene Lagerpositionen
        for line in self.get_open_move_lines():
            product = line["product"]
            covered_product_ids.add(product.id)

            all_lines.append({
                "product": product,
                "product_uom_qty": line["product_uom_qty"],
                "qty_done": 0.0,
                "uom_name": line["uom_name"],
                "lot_names": [],
                "picking_names": line["picking_names"],
                "status": _("Offen"),
                "status_class": "warning",
                "line_type": _("Lager"),
                "is_dropship": False,
                "comment": False,
            })

        # 3. Streckengeschäftspositionen
        for line in self.get_dropship_move_lines():
            product = line["product"]
            covered_product_ids.add(product.id)

            if line["qty_done"] > 0:
                status = _("Erledigt")
                status_class = "success"
            else:
                status = _("Offen")
                status_class = "secondary"

            all_lines.append({
                "product": product,
                "product_uom_qty": line["product_uom_qty"],
                "qty_done": line["qty_done"],
                "uom_name": line["uom_name"],
                "lot_names": line["lot_names"],
                "picking_names": line["picking_names"],
                "status": status,
                "status_class": status_class,
                "line_type": _("Streckengeschäft"),
                "is_dropship": True,
                "comment": False,
            })

        # 4. Dienstleistungen haben in der Regel keine Lagerbewegungen und
        # werden deshalb immer direkt aus den Auftragspositionen übernommen.
        for service in self.get_service_lines():
            line = service["line"]
            product = line.product_id
            uom = line.product_uom_id or product.uom_id

            all_lines.append({
                "product": product,
                "product_uom_qty": line.product_uom_qty or 0.0,
                "qty_done": line.qty_delivered or 0.0,
                "uom_name": uom.name,
                "lot_names": [],
                "picking_names": [],
                "status": service["status"],
                "status_class": service["status_class"],
                "line_type": _("Dienstleistung"),
                "is_dropship": False,
                "comment": line.name or False,
            })

        # 5. Physische Produkte ohne Lager- oder Streckengeschäftsbewegung.
        #
        # Das ist ein Fallback. Sobald das Produkt mindestens in einem
        # Picking vorkommt, wird es oben bereits über Stock Moves ausgegeben.
        for line in self.order_line.filtered(
            lambda line: (
                not line.display_type
                and line.product_id
                and line.product_id.type in ("product", "consu")
                and line.product_id.id not in covered_product_ids
            )
        ):
            if self.state == "sale":
                status = _("Offen")
                status_class = "secondary"
            elif self.state == "cancel":
                status = _("Storniert")
                status_class = "danger"
            else:
                status = _("In Arbeit")
                status_class = "info"

            product = line.product_id
            uom = line.product_uom_id or product.uom_id

            all_lines.append({
                "product": product,
                "product_uom_qty": line.product_uom_qty or 0.0,
                "qty_done": line.qty_delivered or 0.0,
                "uom_name": uom.name,
                "lot_names": [],
                "picking_names": [],
                "status": status,
                "status_class": status_class,
                "line_type": _("Lager"),
                "is_dropship": False,
                "comment": line.name or False,
            })

        return all_lines
