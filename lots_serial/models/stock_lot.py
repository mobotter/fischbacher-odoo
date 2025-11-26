from odoo import models, fields, api
from datetime import datetime, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
# import logging
# _logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
    _inherit = 'stock.lot'
    # Task Id 51088 JC
    tuv_date = fields.Date(string="TÜV Date", help='General inspection date' , tracking=True)
    uvv_date = fields.Date(string="UVV Date", help='Safety inspection date' , tracking=True)
    safety_brake_date = fields.Date(string="Brake Date", help='Brake replacement/inspection date' , tracking=True)

    # Status fields
    tuv_status = fields.Char(string="TÜV Status", compute="_compute_statuses", store=False)
    uvv_status = fields.Char(string="UVV Status", compute="_compute_statuses", store=False)
    safety_brake_status = fields.Char(string="Brake Status", compute="_compute_statuses", store=False)

    def get_color_status(self, reference_date, validity_years=1):
        """
        Status calculation and expiry/warning dates:
        - GREEN → expiry is more than 3 months away
        - ORANGE → less than 3 months left
        - RED → expired
        """
        if not reference_date:
            return "red"

        today = date.today()

        expiry_date = reference_date + relativedelta(years=validity_years)
        # _logger.info("expiry_date: %s", expiry_date)
        warning_date = expiry_date - relativedelta(months=3)
        # _logger.info("warning_date: %s", warning_date)

        if today >= expiry_date:
            status = "red"
        elif today >= warning_date:
            status = "orange"
        else:
            status = "green"

        return status

    @api.depends('tuv_date', 'uvv_date', 'safety_brake_date')
    def _compute_statuses(self):
        for rec in self:
            # Calculate status for TÜV
            tuv_status = self.get_color_status(rec.tuv_date, 1)
            rec.tuv_status = tuv_status

            # Calculate status for UVV
            uvv_status = self.get_color_status(rec.uvv_date, 1)
            rec.uvv_status = uvv_status

            # Calculate status for Safety Brake
            safety_brake_status= self.get_color_status(rec.safety_brake_date, 6)
            rec.safety_brake_status = safety_brake_status
    # Task Id 51088 JC
