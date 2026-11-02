import logging

from odoo import api, models
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


class IrActionsReportIoTInherit(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def render_document(self, device_id_list, res_ids, data=None):
        document = super().render_document(
            device_id_list,
            res_ids,
            data=data,
        )

        if not document or not res_ids:
            return document

        active_model = self.env.context.get("active_model")
        report_xml_id = self.env.context.get("report_xml_id")

        # Never duplicate a report unless it is explicitly a delivery slip.
        if active_model != "stock.picking":
            return document

        # Depending on the Odoo IoT entry point, report_xml_id may be either
        # the report action XML ID or the QWeb report name.
        allowed_report_references = {
            "stock.action_report_delivery",
            "stock.report_deliveryslip",
        }

        if report_xml_id and report_xml_id not in allowed_report_references:
            _logger.info(
                "Skipping delivery-copy logic for report %s on model %s.",
                report_xml_id,
                active_model,
            )
            return document

        picking = self.env["stock.picking"].browse(res_ids[:1]).exists()
        if not picking:
            return document

        copies = max(int(picking.print_copies or 1), 1)

        _logger.info(
            "IoT delivery-slip print: picking=%s, copies=%s, report=%s, devices=%s",
            picking.name,
            copies,
            report_xml_id or "<not provided>",
            device_id_list,
        )

        if copies == 1:
            return document

        if isinstance(document, bytes):
            try:
                merged_document = merge_pdf([document] * copies)
                if merged_document:
                    _logger.info(
                        "Delivery-slip PDF duplicated successfully: picking=%s, copies=%s.",
                        picking.name,
                        copies,
                    )
                    return merged_document
            except Exception:
                _logger.exception(
                    "Could not duplicate delivery-slip PDF for picking %s.",
                    picking.name,
                )

            # Do not return document * copies: concatenating raw PDF bytes is
            # not a valid multipage PDF and can cause corrupt print jobs.
            return document

        if isinstance(document, str):
            _logger.info(
                "Duplicating non-PDF delivery document: picking=%s, copies=%s.",
                picking.name,
                copies,
            )
            return document * copies

        _logger.warning(
            "Unsupported IoT document type %s for picking %s; no copies added.",
            type(document).__name__,
            picking.name,
        )
        return document
