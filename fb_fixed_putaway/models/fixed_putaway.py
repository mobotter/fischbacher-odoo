import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


ROOT_LOCATION_ID = 19360
HOF_LOCATION_ID = 24441
EXCLUDED_LOCATION_IDS = {8, 1085, ROOT_LOCATION_ID}
EXCLUDED_HISTORICAL_LOCATION_IDS = {14963}
FACH_NAME_PATTERN = re.compile(r"^F(0[1-9]|1[0-5])$")


class FbFixedPutawayLine(models.TransientModel):
    _name = "fb.fixed.putaway.line"
    _description = "Vorschlag fuer einen festen Einlagerungsplatz"
    _order = "id"

    wizard_id = fields.Many2one(
        "fb.fixed.putaway.wizard",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        "product.product",
        required=True,
        readonly=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Fester Lagerplatz",
    )
    status = fields.Selection(
        [
            ("unique", "Eindeutig"),
            ("manual", "Pruefen"),
            ("existing", "Regel vorhanden"),
            ("created", "Erstellt"),
        ],
        default="manual",
        readonly=True,
    )
    note = fields.Char(readonly=True)
    apply = fields.Boolean(string="Uebernehmen")
    total_qty = fields.Float(
        string="Gesamtbestand",
        digits="Product Unit of Measure",
        readonly=True,
    )
    suggested_location_count = fields.Integer(
        string="Moegliche Fachorte",
        readonly=True,
    )

    def _is_allowed_location(self, location, root):
        if not location or not location.active:
            return False
        if location.usage != "internal":
            return False
        if location.id in EXCLUDED_LOCATION_IDS:
            return False
        if location.company_id and location.company_id != self.env.company:
            return False
        if not location.parent_path.startswith(root.parent_path):
            return False

        return (
            location.id == HOF_LOCATION_ID
            or bool(FACH_NAME_PATTERN.fullmatch(location.name or ""))
        )

    def _current_candidates(self, root):
        self.ensure_one()

        quants = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("location_id", "child_of", root.id),
                ("location_id.usage", "=", "internal"),
                ("company_id", "in", [False, self.env.company.id]),
            ]
        )

        total_qty = sum(quants.mapped("quantity"))
        quantity_by_location = {}

        for quant in quants:
            location = quant.location_id
            if self._is_allowed_location(location, root):
                quantity_by_location[location.id] = (
                    quantity_by_location.get(location.id, 0.0)
                    + quant.quantity
                )

        positive_location_ids = [
            location_id
            for location_id, quantity in quantity_by_location.items()
            if quantity > 0
        ]
        locations = self.env["stock.location"].browse(
            positive_location_ids
        )

        # Faecher zuerst nach vollstaendigem Pfad;
        # HOF danach, wenn auch Fachbestand vorhanden ist.
        locations = locations.sorted(
            key=lambda location: (
                location.id == HOF_LOCATION_ID,
                location.complete_name or "",
                location.id,
            )
        )
        return total_qty, locations

    def _historical_candidates(self, root):
        self.ensure_one()

        move_lines = self.env["stock.move.line"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("company_id", "=", self.env.company.id),
                ("state", "=", "done"),
                ("quantity_product_uom", ">", 0),
                "|",
                ("location_id", "child_of", root.id),
                ("location_dest_id", "child_of", root.id),
            ],
            order="date desc, id desc",
        )

        candidates_by_id = {}
        for move_line in move_lines:
            for location in (
                move_line.location_id,
                move_line.location_dest_id,
            ):
                if (
                    location.id not in candidates_by_id
                    and location.id
                    not in EXCLUDED_HISTORICAL_LOCATION_IDS
                    and self._is_allowed_location(location, root)
                ):
                    candidates_by_id[location.id] = {
                        "location": location,
                        "date": move_line.date,
                        "move_line_id": move_line.id,
                    }

        # Juengste belegte Nutzung zuerst; bei Gleichstand stabil.
        return sorted(
            candidates_by_id.values(),
            key=lambda candidate: (
                candidate["date"],
                candidate["move_line_id"],
                -candidate["location"].id,
            ),
            reverse=True,
        )

    def _evaluate(self, root):
        self.ensure_one()

        existing = self.env["stock.putaway.rule"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("location_in_id", "=", root.id),
            ],
            limit=1,
        )
        if existing:
            self.write(
                {
                    "status": "existing",
                    "apply": False,
                    "location_id": existing.location_out_id.id or False,
                    "suggested_location_count": 0,
                    "note": _(
                        "Vorhandene Regel wird nicht ueberschrieben."
                    ),
                }
            )
            return

        total_qty, current_locations = self._current_candidates(
            root
        )
        if current_locations:
            self.write(
                {
                    "total_qty": total_qty,
                    "suggested_location_count": len(
                        current_locations
                    ),
                    "location_id": current_locations[0].id,
                    "status": (
                        "unique"
                        if len(current_locations) == 1
                        else "manual"
                    ),
                    "apply": True,
                    "note": _(
                        "Aktueller Bestand: %s zulaessige(r) "
                        "Lagerort(e): %s"
                    )
                    % (
                        len(current_locations),
                        ", ".join(
                            current_locations.mapped(
                                "display_name"
                            )
                        ),
                    ),
                }
            )
            return

        history = self._historical_candidates(root)
        if history:
            first = history[0]
            self.write(
                {
                    "total_qty": total_qty,
                    "suggested_location_count": len(history),
                    "location_id": first["location"].id,
                    "status": "manual",
                    "apply": True,
                    "note": _(
                        "Historischer Vorschlag aus erledigten "
                        "Bewegungen: %s. Bitte vor Uebernahme "
                        "physisch pruefen. Weitere Kandidaten: %s"
                    )
                    % (
                        first["location"].display_name,
                        ", ".join(
                            candidate["location"].display_name
                            for candidate in history[1:]
                        )
                        or _("keine"),
                    ),
                }
            )
            return

        self.write(
            {
                "total_qty": total_qty,
                "suggested_location_count": 0,
                "location_id": False,
                "status": "manual",
                "apply": False,
                "note": _(
                    "Kein aktueller oder historischer zulaessiger "
                    "Ort (F01-F15 oder HOF); bitte manuell pruefen."
                ),
            }
        )

    def action_apply(self):
        if not self.env.user.has_group(
            "stock.group_stock_manager"
        ):
            raise UserError(
                _(
                    "Nur Lageradministratoren duerfen "
                    "Regeln erstellen."
                )
            )

        root = self.env["stock.location"].browse(
            ROOT_LOCATION_ID
        ).exists()
        if (
            not root
            or not root.active
            or root.usage != "internal"
        ):
            raise UserError(
                _(
                    "Hauptlagerort 19360 ist nicht aktiv "
                    "oder nicht intern."
                )
            )

        for line in self:
            if line.status in ("existing", "created"):
                continue

            if line.wizard_id.location_in_id != root:
                raise UserError(
                    _(
                        "Als Eingangsort muss der "
                        "Hauptlagerort 19360 eingestellt sein."
                    )
                )

            if (
                root.company_id
                and root.company_id != self.env.company
            ):
                raise UserError(
                    _("Eingangsort liegt in einer anderen Firma.")
                )

            target = line.location_id
            if not line._is_allowed_location(target, root):
                raise UserError(
                    _(
                        "Ungueltiger Zielort fuer %s: Nur "
                        "Faecher F01-F15 unter %s oder "
                        "WH/LAGER/HOF sind erlaubt."
                    )
                    % (
                        line.product_id.display_name,
                        root.display_name,
                    )
                )

            domain = [
                ("product_id", "=", line.product_id.id),
                ("location_in_id", "=", root.id),
            ]
            if self.env["stock.putaway.rule"].search_count(
                domain
            ):
                raise UserError(
                    _(
                        "Fuer %s existiert bereits eine Regel; "
                        "Vorschau aktualisieren."
                    )
                    % line.product_id.display_name
                )

            self.env["stock.putaway.rule"].create(
                {
                    "product_id": line.product_id.id,
                    "location_in_id": root.id,
                    "location_out_id": target.id,
                }
            )
            line.write(
                {
                    "status": "created",
                    "apply": False,
                    "note": _(
                        "Einlagerungsregel erstellt: %s"
                    )
                    % target.display_name,
                }
            )


class FbFixedPutawayWizard(models.TransientModel):
    _name = "fb.fixed.putaway.wizard"
    _description = "Feste Einlagerungsregeln vorbereiten"
    _rec_name = "name"

    name = fields.Char(
        string="Bezeichnung",
        default="Feste Einlagerungsregeln vorbereiten",
        readonly=True,
    )
    location_in_id = fields.Many2one(
        "stock.location",
        required=True,
        string="Eingangsort",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Einzelprodukt",
    )
    line_ids = fields.One2many(
        "fb.fixed.putaway.line",
        "wizard_id",
        string="Vorschau",
    )
    new_proposal_count = fields.Integer(
        string="Neue Vorschlaege",
        compute="_compute_new_proposal_count",
    )

    @api.depends(
        "line_ids",
        "line_ids.apply",
        "line_ids.status",
    )
    def _compute_new_proposal_count(self):
        for wizard in self:
            wizard.new_proposal_count = len(
                wizard.line_ids.filtered(
                    lambda line: line.apply
                    and line.status not in (
                        "existing",
                        "created",
                    )
                )
            )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if "location_in_id" in fields_list:
            vals["location_in_id"] = ROOT_LOCATION_ID
        return vals

    def action_preview(self):
        self.ensure_one()

        if not self.env.user.has_group(
            "stock.group_stock_manager"
        ):
            raise UserError(
                _(
                    "Nur Lageradministratoren duerfen "
                    "die Vorschau laden."
                )
            )

        root = self.env["stock.location"].browse(
            ROOT_LOCATION_ID
        ).exists()
        if not root or self.location_in_id != root:
            raise UserError(
                _(
                    "Eingangsort muss der Hauptlagerort "
                    "19360 sein."
                )
            )

        if not root.active or root.usage != "internal":
            raise UserError(
                _(
                    "Eingangsort muss aktiv und "
                    "intern sein."
                )
            )

        if (
            root.company_id
            and root.company_id != self.env.company
        ):
            raise UserError(
                _("Eingangsort liegt in einer anderen Firma.")
            )

        self.line_ids.unlink()

        if self.product_id:
            products = self.product_id
        else:
            products = self.env["product.product"].search(
                [
                    ("active", "=", True),
                    ("is_storable", "=", True),
                    (
                        "company_id",
                        "in",
                        [False, self.env.company.id],
                    ),
                ]
            )

        existing_rules = self.env["stock.putaway.rule"].search(
            [
                ("location_in_id", "=", root.id),
                ("product_id", "in", products.ids),
            ]
        )
        products_with_rule = set(
            existing_rules.mapped("product_id").ids
        )

        products_without_rule = products.filtered(
            lambda product: product.id not in products_with_rule
        )

        for product in products_without_rule:
            line = self.env[
                "fb.fixed.putaway.line"
            ].create(
                {
                    "wizard_id": self.id,
                    "product_id": product.id,
                }
            )
            line._evaluate(root)

        return self._reopen()

    def action_apply_selected(self):
        self.ensure_one()
        self.line_ids.filtered("apply").action_apply()
        return self._reopen()

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Feste Einlagerungsregeln"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_fb_open_fixed_putaway(self):
        self.ensure_one()

        if len(self.product_variant_ids) != 1:
            raise UserError(
                _(
                    "Bei mehreren Varianten bitte die "
                    "jeweilige Variante einzeln waehlen."
                )
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Feste Einlagerungsregeln"),
            "res_model": "fb.fixed.putaway.wizard",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_product_id":
                    self.product_variant_id.id,
            },
        }
