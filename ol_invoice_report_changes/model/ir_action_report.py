import logging
from odoo.addons.account.models.ir_actions_report import IrActionsReport

_logger = logging.getLogger(__name__)


def _pre_render_qweb_pdf(self, report_ref, res_ids=None, data=None):
    _logger.info("===== PDF PRE-RENDER TRIGGERED =====")
    _logger.info("Report Ref: %s", report_ref)
    _logger.info("Res IDs: %s", res_ids)
    _logger.info("Data: %s", data)

    result = super(IrActionsReport, self)._pre_render_qweb_pdf(
        report_ref,
        res_ids=res_ids,
        data=data
    )

    _logger.info("===== PDF PRE-RENDER COMPLETED =====")

    return result

IrActionsReport._pre_render_qweb_pdf= _pre_render_qweb_pdf
