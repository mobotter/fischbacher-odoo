from odoo import models, fields, api, _
from odoo.exceptions import (
    AccessError,
    RedirectWarning,
    UserError,
    ValidationError,
)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Status erweitern - ondelete auf 'set null' gesetzt
    state = fields.Selection(
        selection_add=[('accepted', "Order Accepted by Client")],
        ondelete={'accepted': 'set null'}
    )
    
    # Abo-Status erweitern - ondelete auf 'set null' gesetzt
    subscription_state = fields.Selection(
        selection_add=[('accepted', 'Accepted')],
        ondelete={'accepted': 'set null'}
    )
    
    quotation_line_ids = fields.One2many(
        'sale.quotation.line',
        'order_id',
        string='Quotation Lines'
    )

    def action_accept_by_client(self):
        for order in self:
            order.state = 'accepted'
            if order.is_subscription:
                order.subscription_state = 'accepted'
    
    def action_reset_to_quotation(self):
        for record in self:
            record.state = 'draft'
            if record.is_subscription:
                record.subscription_state = '1_draft'

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then return error message. """
        error = super()._confirmation_error_message()
        if error and self.state == 'accepted' and "state requiring confirmation" in str(error):
            return False
        return error

    @api.constrains('plan_id', 'state', 'order_line')
    def _constraint_subscription_plan(self):
        for so in self:
            if so.state in ['draft', 'cancel', 'accepted'] or so.subscription_state == '7_upsell':
                continue
            if so.subscription_id and not so.subscription_state:
                continue

            if so.has_recurring_line and not so.plan_id:
                raise UserError(_('Please add a recurring plan on the subscription or remove the recurring product.'))
            if so.plan_id and not so.has_recurring_line:
                raise UserError(_('Please add a recurring product in the subscription or remove the recurring plan.'))

    def action_quotation_send_subscription(self):
        self.filtered(lambda so: so.state in ('draft', 'sent', 'accepted')).order_line._validate_analytic_distribution()
        lang = self.env.context.get('lang')

        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'proforma': self.env.context.get('proforma', False),
        }

        if len(self) > 1:
            ctx['default_composition_mode'] = 'mass_mail'
        else:
            ctx.update({
                'force_email': True,
                'model_description': self.with_context(lang=lang).type_name,
            })
            if not self.env.context.get('hide_default_template'):
                mail_template = self._find_mail_template_subscription()
                if mail_template:
                    ctx.update({
                        'default_template_id': mail_template.id,
                        'mark_so_as_sent': True,
                    })
                if mail_template and mail_template.lang:
                    lang = mail_template._render_lang(self.ids)[self.id]
            else:
                for order in self:
                    order._portal_ensure_token()

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
        if (
            self.env.context.get('check_document_layout')
            and not self.env.context.get('discard_logo_check')
            and self.env.is_admin()
            and not self.env.company.external_report_layout_id
        ):
            layout_action = self.env['ir.actions.report']._action_configure_external_report_layout(action)
            action.pop('close_on_report_download', None)
            layout_action['context']['dialog_size'] = 'extra-large'
            return layout_action
        return action

    def _find_mail_template_subscription(self):
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            return self.env.ref('ol_sale_subscription_extensions.email_template_edi_sale_subscription', raise_if_not_found=False)
        else:
            return self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
