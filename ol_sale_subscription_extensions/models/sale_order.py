from odoo import models, fields, api, _
from odoo.exceptions import (
    AccessError,
    RedirectWarning,
    UserError,
    ValidationError,
)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
        selection_add=[
            ('accepted', "Order Accepted by Client"),
            ('sale',)
        ],
        ondelete={'accepted': 'set null'}
    )

    subscription_state = fields.Selection(
        selection_add=[('accepted', 'Accepted')],
        ondelete={'accepted': 'set null'}
    )

    quotation_line_ids = fields.One2many(
        'sale.quotation.line',
        'order_id',
        string='Quotation Lines'
    )

    quotation_template_id = fields.Many2one(
        'sale.order.template',
        string='Quotation Lines Template',
        help='Template used to fill the Quotation Lines tab.',
    )

    @api.onchange('quotation_template_id')
    def _onchange_quotation_template_id(self):
        for order in self:
            if not order.quotation_template_id:
                continue
    
            new_lines = []
            for line in order.quotation_template_id.sale_order_template_line_ids.sorted(lambda l: l.sequence):
                vals = {
                    'sequence': line.sequence,
                    'display_type': line.display_type,
                    'name': line.name,
                }
    
                if not line.display_type:
                    vals.update({
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom_id.id,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'tax_id': [(6, 0, line.tax_id.ids)],
                    })
    
                new_lines.append((0, 0, vals))
    
            order.quotation_line_ids = [(5, 0, 0)] + new_lines

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
        invalid_orders = self.filtered(lambda o: o.state not in ('draft', 'sent', 'accepted'))
        if invalid_orders:
            return _("Some orders are not in a state requiring confirmation.")
        return False

    def action_confirm(self):
        accepted_orders = self.filtered(lambda o: o.state == 'accepted')
        if accepted_orders:
            accepted_orders.write({'state': 'sent'})
        return super().action_confirm()

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
