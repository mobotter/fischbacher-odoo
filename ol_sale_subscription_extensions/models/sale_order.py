from odoo import models, fields, api, _
from odoo.exceptions import (
    AccessError,
    RedirectWarning,
    UserError,
    ValidationError,
)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Erweiterung des Base-Order-State
    state = fields.Selection(
        selection_add=[('accept', "Order Accepted by Client")],
        ondelete={'accept': 'set null'}
    )
    
    # Erweiterung des Subscription-Badge-State
    subscription_state = fields.Selection(
        selection_add=[('5_accepted', "Accepted by Client")],
        ondelete={'5_accepted': 'set null'}
    )

    quotation_line_ids = fields.One2many(
        'sale.quotation.line',
        'order_id',
        string='Quotation Lines'
    )

    # Verhindert, dass Odoo das Abo in der Liste auf "Abgelaufen" (6_churn) setzt, 
    # nur weil unser Custom-State ("accept") aktiv ist.
    @api.depends('state', 'is_subscription')
    def _compute_subscription_state(self):
        super()._compute_subscription_state()
        for order in self:
            if order.is_subscription and order.state == 'accept':
                order.subscription_state = '5_accepted'

    def action_accept_by_client(self):
        for order in self:
            order.state = 'accept'
            # Explizites Setzen, damit das UI sofort reagiert
            if order.is_subscription:
                order.subscription_state = '5_accepted'
    
    def action_reset_to_quotation(self):
        for record in self:
            record.state = 'draft'
            if record.is_subscription:
                record.subscription_state = '1_draft'

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then return error message. """
        error = super()._confirmation_error_message()
        
        # Odoo blockiert standardmäßig alles, was nicht 'draft' oder 'sent' ist.
        # Wenn der Fehler geworfen wird, unser Auftrag aber auf 'accept' steht,
        # heben wir diesen spezifischen Blockade-Fehler auf.
        if error and self.state == 'accept' and "state requiring confirmation" in str(error):
            return False
            
        return error

    @api.constrains('plan_id', 'state', 'order_line')
    def _constraint_subscription_plan(self):
        for so in self:
            # Erlaubt nun auch den Status 'accept' in der Base-Prüfung
            if so.state in ['draft', 'cancel', 'accept'] or so.subscription_state == '7_upsell':
                continue
            if so.subscription_id and not so.subscription_state:
                # so created before merge sale.subscription into sale.order upgrade.
                continue

            if so.has_recurring_line and not so.plan_id:
                raise UserError(_('Please add a recurring plan on the subscription or remove the recurring product.'))
            if so.plan_id and not so.has_recurring_line:
                raise UserError(_('Please add a recurring product in the subscription or remove the recurring plan.'))

    def action_quotation_send_subscription(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.filtered(lambda so: so.state in ('draft', 'sent', 'accept')).order_line._validate_analytic_distribution()
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
            layout_action = self.env['ir.actions.report']._action_configure_external_report_layout(
                action,
            )
            action.pop('close_on_report_download', None)
            layout_action['context']['dialog_size'] = 'extra-large'
            return layout_action
        return action

    def _find_mail_template_subscription(self):
        """ Get the appropriate mail template for the current sales order based on its state. """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            return self.env.ref('ol_sale_subscription_extensions.email_template_edi_sale_subscription', raise_if_not_found=False)
        else:
            return self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
