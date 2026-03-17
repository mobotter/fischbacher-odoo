from odoo import models, fields, api, _
from odoo.exceptions import (
    AccessError,
    RedirectWarning,
    UserError,
    ValidationError,
)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # 1. KORREKTUR: selection_add anstelle von harter Überschreibung
    state = fields.Selection(
        selection_add=[('accept', "Order Accepted by Client")],
        ondelete={'accept': 'set default'}
    )
    
    quotation_line_ids = fields.One2many(
        'sale.quotation.line',
        'order_id',
        string='Quotation Lines'
    )

    def action_accept_by_client(self):
        for order in self:
            order.state = 'accept'
    
    def action_reset_to_quotation(self):
        for record in self:
            record.state = 'draft'

    # 2. KORREKTUR: Super-Aufruf, um Basis-Checks (wie fehlende Produkte) zu behalten
    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then return error message. """
        error = super()._confirmation_error_message()
        
        # Odoo blockiert standardmäßig alles, was nicht 'draft' oder 'sent' ist.
        # Wenn der Fehler geworfen wird, unser Auftrag aber auf 'accept' steht,
        # heben wir diesen spezifischen Blockade-Fehler auf.
        if error and self.state == 'accept' and "state requiring confirmation" in str(error):
            return False
            
        return error

    # 3. KORREKTUR: Kompatibilität mit dem Subscription-Modell sichergestellt
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
        # Hinzufügen von 'accept' in die gefilterte Liste für Analytic Distribution Validation
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
            # Need to remove this context for windows action
            action.pop('close_on_report_download', None)
            layout_action['context']['dialog_size'] = 'extra-large'
            return layout_action
        return action

    # 4. KORREKTUR: Sinnvolle if/else Logik für die E-Mail-Templates
    def _find_mail_template_subscription(self):
        """ Get the appropriate mail template for the current sales order based on its state. """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            # Rückgabe für Quotation / Proforma / Accept
            return self.env.ref('ol_sale_subscription_extensions.email_template_edi_sale_subscription', raise_if_not_found=False)
        else:
            # Rückgabe für bestätigte Sales Orders (zuvor stand hier exakt dasselbe Template)
            return self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
