# Author: Moritz Kern
# Company: Fischbacher GmbH + Co. KG

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    repair_id = fields.Many2one(
        "repair.order",
        string="Repair Order",
        help="Link to the repair order (only for repair orders).",
    )

    purchase_no = fields.Char(
        string="Purchase",
        help="Internal purchase reference or purchase order number.",
    )

    order_number = fields.Char(
        string="Order Number",
        help="Internal order number for this sales order.",
    )

    # Temporary compatibility field for old views / Studio leftovers
    is_rent = fields.Boolean(
        string="Rent",
        compute="_compute_is_rent",
    )

    lease_agreement_no = fields.Char(
        string="DSP-Auftragsnummer",
        copy=False,
        help="Bisherige bzw. externe Auftragsnummer aus DSP3.",
    )

    mk_rental_contract_id = fields.Many2one(
        comodel_name="sale.order",
        string="Auftragsnummer / Mietvertragsnummer",
        domain=(
            "['|', '|', '|', "
            "('id', '=', id), "
            "('is_rental_order', '=', True), "
            "('is_subscription', '=', True), "
            "('plan_id', '!=', False)]"
        ),
        check_company=True,
        ondelete="restrict",
        index=True,
        copy=False,
        help=(
            "Zugehörigen Mietpark-Vertrag oder GEDA-Abonnementvertrag "
            "auswählen. Auch der eigene gespeicherte Auftrag kann "
            "ausgewählt werden."
        ),
    )

    mk_linked_sale_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="mk_rental_contract_id",
        string="Zusätzliche Verkaufsaufträge",
        help=(
            "Verkaufsangebote und Verkaufsaufträge, die diesem "
            "Mietvertrag zugeordnet sind. Bei einem Selbstverweis "
            "ist auch der Vertrag selbst in dieser Beziehung enthalten."
        ),
    )

    hide_total = fields.Boolean(
        string="Hide Total Amount",
    )

    client_order_name = fields.Text(
        string="Ordered by",
        help="Name of the person or department who placed this order.",
    )

    client_order_number = fields.Char(
        string="Your Order Number",
        help="The customer's internal order or reference number for this order.",
    )

    offer_intro_text = fields.Text(
        string="Offer Introduction Text",
        default=lambda self: _(
            "Dear Sir or Madam,\n"
            "Thank you for your interest. Please find our quotation attached.\n"
            "We are happy to answer any questions you may have."
        ),
        help=(
            "Custom introduction text displayed on the quotation and "
            "sales order confirmation report."
        ),
    )

    delivery_time = fields.Text(
        string="Delivery time",
        translate=True,
        default="To be agreed",
        help=(
            "Specify the estimated delivery time. This information "
            "will be displayed on the quotation and sales order."
        ),
    )

    billing_period_start = fields.Date(
        string="Billing Period Start",
        compute="_compute_billing_period",
        store=True,
        help=(
            "Start date of the current billing period, "
            "calculated from the next invoice date."
        ),
    )

    billing_period_end = fields.Date(
        string="Billing Period End",
        compute="_compute_billing_period",
        store=True,
        help=(
            "End date of the current billing period, "
            "calculated from the next invoice date."
        ),
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._set_ebay_payment_term()
        return orders

    def write(self, vals):
        result = super().write(vals)

        if "start_date" in vals or "plan_id" in vals:
            self._recompute_next_invoice_date_from_start_date()

        if (
            "tag_ids" in vals
            and not self.env.context.get("skip_ebay_payment_term")
        ):
            self._set_ebay_payment_term()

        return result

    # -------------------------------------------------------------------------
    # Rental contract links
    # -------------------------------------------------------------------------

    @api.model
    def _mk_get_rental_contract_domain(self):
        """
        Return the base domain for rental and subscription contracts.

        The sale.order field adds the current order to its client-side
        domain so that regular sales orders can select themselves too.

        This base domain can also be used by the repair.order extension.
        """
        return [
            "|",
            "|",
            ("is_rental_order", "=", True),
            ("is_subscription", "=", True),
            ("plan_id", "!=", False),
        ]

    def _mk_is_rental_contract(self):
        """Return whether this order is a rental or subscription contract."""
        self.ensure_one()

        return bool(
            self.is_rental_order
            or self.is_subscription
            or self.plan_id
        )

    @api.constrains("mk_rental_contract_id")
    def _check_mk_rental_contract_id(self):
        """
        Allow selecting the current order itself.

        Links to other orders must point to rental or subscription
        contracts. Self-references are valid endpoints.

        Circular links between different orders are rejected.
        """
        for order in self:
            contract = order.mk_rental_contract_id

            if not contract:
                continue

            # Der eigene Auftrag darf immer ausgewählt werden.
            if contract == order:
                continue

            if not contract._mk_is_rental_contract():
                raise ValidationError(
                    _(
                        "Bitte einen Mietpark-Vertrag, einen "
                        "GEDA-Abonnementvertrag oder den eigenen "
                        "Auftrag auswählen."
                    )
                )

            visited_ids = {order.id}

            while contract:
                if contract.id in visited_ids:
                    raise ValidationError(
                        _(
                            "Eine zyklische Verknüpfung zwischen "
                            "verschiedenen Aufträgen ist nicht erlaubt."
                        )
                    )

                visited_ids.add(contract.id)

                next_contract = contract.mk_rental_contract_id

                # Ein Selbstverweis ist erlaubt und beendet die Prüfung.
                if next_contract == contract:
                    break

                contract = next_contract

    def action_mk_linked_sales(self):
        """
        Open additional sales orders belonging to this contract.

        Exclude the current order itself from the additional orders,
        even when the contract points to itself.
        """
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Zusätzliche Verkaufsaufträge"),
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [
                ("mk_rental_contract_id", "=", self.id),
                ("id", "!=", self.id),
            ],
            "context": {
                "default_mk_rental_contract_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_mk_linked_repairs(self):
        """
        Open repairs belonging to this contract.

        Requires mk_rental_contract_id to be added to repair.order.
        """
        self.ensure_one()

        if (
            "mk_rental_contract_id"
            not in self.env["repair.order"]._fields
        ):
            raise ValidationError(
                _(
                    "Die Mietvertragsverknüpfung ist im Reparaturmodell "
                    "noch nicht eingerichtet. Bitte zuerst das Feld "
                    "'mk_rental_contract_id' in repair.order ergänzen "
                    "und das Modul aktualisieren."
                )
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Zugeordnete Reparaturen"),
            "res_model": "repair.order",
            "view_mode": "list,form",
            "domain": [
                ("mk_rental_contract_id", "=", self.id),
            ],
            "context": {
                "default_mk_rental_contract_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_company_id": self.company_id.id,
            },
        }

    # -------------------------------------------------------------------------
    # eBay payment terms
    # -------------------------------------------------------------------------

    def _set_ebay_payment_term(self):
        """
        Set payment term 'Betrag dankend erhalten' for orders tagged as eBay.

        The tag comparison ignores capitalization, e.g. ebay, eBay and EBAY
        all match. The payment term is searched company-specific first.
        """
        payment_term_model = self.env["account.payment.term"]

        payment_term = payment_term_model.search(
            [
                ("name", "=", "Betrag dankend erhalten"),
                ("company_id", "=", self.env.company.id),
                ("active", "=", True),
            ],
            limit=1,
        )

        if not payment_term:
            payment_term = payment_term_model.search(
                [
                    ("name", "=", "Betrag dankend erhalten"),
                    ("company_id", "=", False),
                    ("active", "=", True),
                ],
                limit=1,
            )

        # Fallback for the existing payment-term record supplied by you.
        if not payment_term:
            payment_term = payment_term_model.browse(29).exists()

        if not payment_term:
            return

        ebay_orders = self.filtered(
            lambda order: any(
                tag.name
                and tag.name.strip().casefold() == "ebay"
                for tag in order.tag_ids
            )
        )

        if ebay_orders:
            ebay_orders.with_context(
                skip_ebay_payment_term=True
            ).write(
                {
                    "payment_term_id": payment_term.id,
                }
            )

    # -------------------------------------------------------------------------
    # Report filenames
    # -------------------------------------------------------------------------

    def _get_sale_report_filename(self):
        """Return the localized filename for the standard sale report."""
        self.ensure_one()

        if self.state in ("draft", "sent"):
            return _("Quotation - %s") % (
                self.name or _("Draft")
            )

        if self.state == "sale":
            return _("Order Confirmation - %s") % (
                self.name or _("Draft")
            )

        return _("Order - %s") % (
            self.name or _("Draft")
        )

    def _get_order_confirmation_report_filename(self):
        """Return the localized filename for the dedicated confirmation report."""
        self.ensure_one()

        return _("Order Confirmation - %s") % (
            self.name or _("Draft")
        )

    # -------------------------------------------------------------------------
    # Rental and subscription billing
    # -------------------------------------------------------------------------

    @api.depends("plan_id", "is_subscription")
    def _compute_is_rent(self):
        for order in self:
            order.is_rent = bool(
                (
                    "plan_id" in order._fields
                    and order.plan_id
                )
                or (
                    "is_subscription" in order._fields
                    and order.is_subscription
                )
            )

    def _get_billing_timing(self):
        self.ensure_one()

        if (
            "plan_id" in self._fields
            and self.plan_id
            and "billing_timing" in self.plan_id._fields
            and self.plan_id.billing_timing
        ):
            return self.plan_id.billing_timing

        return "arrears"

    def _recompute_next_invoice_date_from_start_date(self):
        for order in self:
            if not order.plan_id:
                continue

            start_date = False

            if "start_date" in order._fields and order.start_date:
                start_date = order.start_date
            elif order.date_order:
                start_date = fields.Date.to_date(order.date_order)

            if not start_date:
                continue

            billing_timing = order._get_billing_timing()

            if billing_timing == "arrears":
                order.next_invoice_date = start_date + relativedelta(days=28)
            else:
                order.next_invoice_date = start_date

    @api.onchange("start_date", "plan_id")
    def _onchange_start_date_or_plan_id_recompute_next_invoice_date(self):
        self._recompute_next_invoice_date_from_start_date()

    def _calculate_billing_period_dates(self):
        self.ensure_one()

        if not self.next_invoice_date:
            return False, False

        billing_timing = self._get_billing_timing()

        if billing_timing == "arrears":
            billing_end = self.next_invoice_date - relativedelta(days=1)
            billing_start = billing_end - relativedelta(days=27)
        else:
            billing_start = self.next_invoice_date
            billing_end = billing_start + relativedelta(days=27)

        return billing_start, billing_end

    @api.depends("next_invoice_date", "plan_id")
    def _compute_billing_period(self):
        for order in self:
            billing_start, billing_end = (
                order._calculate_billing_period_dates()
            )

            order.billing_period_start = billing_start
            order.billing_period_end = billing_end

    def _get_billing_period_dates_for_report(self):
        self.ensure_one()

        if self.billing_period_start and self.billing_period_end:
            return (
                self.billing_period_start,
                self.billing_period_end,
            )

        return self._calculate_billing_period_dates()

    def _get_billing_period_label_for_report(self):
        self.ensure_one()

        billing_start, billing_end = (
            self._get_billing_period_dates_for_report()
        )

        if not billing_start or not billing_end:
            return False

        return _("Billing period from %(start)s to %(end)s") % {
            "start": billing_start.strftime("%d.%m.%Y"),
            "end": billing_end.strftime("%d.%m.%Y"),
        }

    # -------------------------------------------------------------------------
    # Invoice preparation
    # -------------------------------------------------------------------------

    def _prepare_invoice(self):
        self.ensure_one()

        vals = super()._prepare_invoice()

        billing_start, billing_end = (
            self._get_billing_period_dates_for_report()
        )

        vals.update(
            {
                "invoice_user_id": (
                    self.user_id.id
                    if self.user_id
                    else False
                ),
                "rental_billing_period_start": billing_start,
                "rental_billing_period_end": billing_end,
                "lease_agreement_no": self.lease_agreement_no,
            }
        )

        invoice_fields = self.env["account.move"]._fields

        # Transfer the selected contract to the invoice when the
        # corresponding account.move field is available.
        #
        # Without a selected contract, use the originating sales order
        # so that the invoice can resolve its order reference without
        # introducing an additional contract-number field.
        if "mk_rental_contract_id" in invoice_fields:
            contract = self.mk_rental_contract_id or self

            vals["mk_rental_contract_id"] = contract.id

        return vals

    def _get_invoice_grouping_keys(self):
        """
        Keep invoices with different contract references or DSP numbers
        separate when the corresponding invoice fields are available.
        """
        grouping_keys = list(
            super()._get_invoice_grouping_keys()
        )

        invoice_fields = self.env["account.move"]._fields

        for field_name in (
            "lease_agreement_no",
            "mk_rental_contract_id",
        ):
            if (
                field_name in invoice_fields
                and field_name not in grouping_keys
            ):
                grouping_keys.append(field_name)

        return grouping_keys

    # -------------------------------------------------------------------------
    # Mail templates
    # -------------------------------------------------------------------------

    def _find_mail_template(self):
        self.ensure_one()

        if self.env.context.get("proforma"):
            return self.env.ref(
                "ol_invoice_report_changes.email_template_edi_sale_proforma",
                raise_if_not_found=False,
            )

        return super()._find_mail_template()

    # -------------------------------------------------------------------------
    # Report sections
    # -------------------------------------------------------------------------

    def _get_report_sections_for_pdf(self):
        """
        Build report sections in the stored position order.

        Products and notes are collected together in ordered_lines.
        The existing product_lines and note_lines remain available
        for compatibility with other report templates.
        """
        self.ensure_one()

        def _field_is_true(record, field_name):
            return bool(
                record
                and field_name in record._fields
                and record[field_name]
            )

        def _new_block(section_line=None):
            return {
                "title": section_line.name if section_line else False,
                "is_optional": (
                    _field_is_true(section_line, "is_optional")
                    if section_line
                    else False
                ),
                "hide_prices": (
                    _field_is_true(section_line, "hide_price_section")
                    if section_line
                    else False
                ),
                "hide_composition": (
                    _field_is_true(
                        section_line,
                        "hide_composition_section",
                    )
                    if section_line
                    else False
                ),
                "subtotal": 0.0,
                "product_lines": [],
                "note_lines": [],
                "ordered_lines": [],
            }

        result = []
        current = _new_block()
        lines_to_process = self.order_line

        is_sub = bool(
            (
                "plan_id" in self._fields
                and self.plan_id
            )
            or (
                "is_subscription" in self._fields
                and self.is_subscription
            )
        )

        if is_sub:
            if (
                "quotation_lines" in self._fields
                and self.quotation_lines
            ):
                lines_to_process = self.quotation_lines
            elif (
                "quotation_line_ids" in self._fields
                and self.quotation_line_ids
            ):
                lines_to_process = self.quotation_line_ids

        if "sequence" in lines_to_process._fields:
            lines_to_process = lines_to_process.sorted(
                key=lambda line: (line.sequence, line.id)
            )

        for line in lines_to_process:
            display_type = (
                line.display_type
                if "display_type" in line._fields
                else False
            )

            if display_type == "line_section":
                if current["title"] or current["ordered_lines"]:
                    result.append(current)

                current = _new_block(line)
                continue

            if display_type == "line_note":
                current["note_lines"].append(line)
                current["ordered_lines"].append(
                    {
                        "type": "note",
                        "line": line,
                        "show_prices": False,
                    }
                )
                continue

            line_dict = {
                "line": line,
                "show_prices": not current["hide_prices"],
            }

            current["product_lines"].append(line_dict)
            current["ordered_lines"].append(
                {
                    "type": "product",
                    **line_dict,
                }
            )

            if "price_subtotal" in line._fields:
                current["subtotal"] += line.price_subtotal
            else:
                quantity = getattr(
                    line,
                    "product_uom_qty",
                    getattr(line, "quantity", 0.0),
                )
                price = getattr(line, "price_unit", 0.0)
                current["subtotal"] += quantity * price

        if current["title"] or current["ordered_lines"]:
            result.append(current)

        return result
