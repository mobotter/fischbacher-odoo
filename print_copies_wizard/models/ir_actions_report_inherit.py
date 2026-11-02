import logging
from uuid import uuid4

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    iot_print_copies = fields.Integer(
        string="Standard IoT-Kopien",
        default=1,
        help=(
            "Gesamtzahl der Druckexemplare pro Dokument und ausgewähltem "
            "IoT-Drucker. Zusätzliche Exemplare werden über den "
            "IoT-WebSocket-Kanal gesendet."
        ),
    )

    def _get_print_copies(self):
        """Return the total number of copies for this report."""
        self.ensure_one()
        return max(self.iot_print_copies or 1, 1)

    def render_document(self, device_id_list, res_ids, data=None):
        """
        Keep the standard client print and enqueue additional copies.

        The standard result contains Base64-encoded document data.
        Extra copies use the same message format as the IoT WebSocket client.
        """
        self.ensure_one()

        documents = super().render_document(
            device_id_list,
            res_ids,
            data=data,
        )

        copies = self._get_print_copies()

        _logger.info(
            "IoT copies: report_id=%s, report=%s, copies=%s, "
            "devices=%s, res_ids=%s, result_type=%s",
            self.id,
            self.report_name,
            copies,
            device_id_list,
            res_ids,
            type(documents).__name__,
        )

        if not documents or not device_id_list or copies <= 1:
            return documents

        if not isinstance(documents, list):
            _logger.warning(
                "IoT copies: unexpected return type %s for report %s; "
                "no extra copies queued.",
                type(documents).__name__,
                self.report_name,
            )
            return documents

        devices = (
            self.env["iot.device"]
            .sudo()
            .browse(device_id_list)
            .exists()
        )
        devices_by_id = {device.id: device for device in devices}

        channel = self.env["iot.channel"].sudo()
        queued_count = 0
        failed_count = 0

        # Process each original job separately so that every document is
        # sent only to the device assigned to it by the standard method.
        for job_index, document in enumerate(documents, start=1):
            if not isinstance(document, dict):
                _logger.warning(
                    "IoT copies: unsupported job type %s at index %s "
                    "for report %s.",
                    type(document).__name__,
                    job_index,
                    self.report_name,
                )
                continue

            device = devices_by_id.get(document.get("deviceId"))
            if device is None:
                _logger.warning(
                    "IoT copies: unknown deviceId=%r in job %s "
                    "for report %s.",
                    document.get("deviceId"),
                    job_index,
                    self.report_name,
                )
                continue

            document_base64 = self._extract_document_bytes(document)
            if not document_base64:
                _logger.warning(
                    "IoT copies: no usable Base64 document in job %s "
                    "for report %s; device=%s.",
                    job_index,
                    self.report_name,
                    device.display_name,
                )
                continue

            for copy_index in range(1, copies):
                session_id = str(uuid4())
                print_id = self._get_extra_copy_print_id(
                    copy_index,
                    device,
                    res_ids,
                )

                message = {
                    "iot_identifiers": [device.iot_id.identifier],
                    "iot_identifier": device.iot_id.identifier,
                    "device_identifiers": [device.identifier],
                    "device_identifier": device.identifier,
                    "session_id": session_id,
                    "action_unique_id": session_id,
                    "document": document_base64,
                    "print_id": print_id,
                }

                try:
                    # Roll back a failed extra enqueue independently.
                    with self.env.cr.savepoint():
                        channel.send_message(
                            message,
                            message_type="iot_action",
                        )
                except Exception:
                    failed_count += 1
                    _logger.exception(
                        "IoT copies: failed to queue extra copy %s/%s; "
                        "report=%s, job=%s, device=%s, "
                        "session_id=%s, print_id=%s.",
                        copy_index,
                        copies - 1,
                        self.report_name,
                        job_index,
                        device.display_name,
                        session_id,
                        print_id,
                    )
                else:
                    queued_count += 1
                    _logger.info(
                        "IoT copies: queued extra copy %s/%s; "
                        "report=%s, job=%s, device=%s, "
                        "base64_length=%s, session_id=%s, print_id=%s.",
                        copy_index,
                        copies - 1,
                        self.report_name,
                        job_index,
                        device.display_name,
                        len(document_base64),
                        session_id,
                        print_id,
                    )

        _logger.info(
            "IoT copies: finished enqueueing; report=%s, "
            "original_jobs=%s, copies=%s, "
            "extra_jobs_queued=%s, extra_jobs_failed=%s.",
            self.report_name,
            len(documents),
            copies,
            queued_count,
            failed_count,
        )

        # The browser receives the unchanged original jobs and handles
        # the normal first copy through the standard IoT client.
        return documents

    @api.model
    def _extract_document_bytes(self, document):
        """
        Return the existing Base64 payload as an ASCII string.

        The method name is retained for compatibility. The returned value
        is NOT raw PDF/ZPL content and must NOT be Base64-decoded here.
        """
        if isinstance(document, list):
            if not document:
                return False
            document = document[0]

        if isinstance(document, dict):
            payload = document.get("document")
        else:
            payload = document

        if isinstance(payload, bytes):
            try:
                return payload.decode("ascii")
            except UnicodeDecodeError:
                _logger.warning(
                    "IoT copies: document bytes are not ASCII Base64."
                )
                return False

        if isinstance(payload, str):
            return payload

        _logger.warning(
            "IoT copies: unsupported document payload type %s.",
            type(payload).__name__,
        )
        return False

    def _get_extra_copy_print_id(self, copy_index, device, res_ids):
        """Build a new print ID for every extra print attempt."""
        self.ensure_one()

        record_id = res_ids[0] if res_ids else "no-record"

        return (
            f"extra_copy_"
            f"{self.id}_"
            f"{record_id}_"
            f"{device.id}_"
            f"{copy_index}_"
            f"{uuid4().hex}"
        )
