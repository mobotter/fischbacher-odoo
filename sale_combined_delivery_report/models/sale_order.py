from odoo import models

# States die als "erledigt" gelten
DONE_STATES = ('done',)
# States die als "offen / geplant" gelten
OPEN_STATES = ('waiting', 'confirmed', 'assigned', 'partially_available')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_combined_delivery_slip(self):
        """Button-Aktion: Öffnet den kombinierten Lieferschein als PDF."""
        return self.env.ref(
            'sale_combined_delivery_report.action_report_combined_delivery'
        ).report_action(self)

    def _get_outgoing_pickings(self, states):
        """Hilfsmethode: Gibt Ausgangslieferungen des Auftrags nach States zurück."""
        return self.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing' and p.state in states
        ).sorted(key=lambda p: p.date_done or p.scheduled_date or p.create_date)

    def get_done_pickings(self):
        """Alle abgeschlossenen Ausgangslieferungen, sortiert nach Datum."""
        return self._get_outgoing_pickings(DONE_STATES)

    def get_open_pickings(self):
        """Alle offenen/geplanten Ausgangslieferungen, sortiert nach geplantem Datum."""
        return self._get_outgoing_pickings(OPEN_STATES)

    def get_done_move_lines(self):
        """Aggregiert erledigte Move-Lines über alle done-Lieferungen.
        Gleiche Produkte werden zusammengefasst.
        """
        return self._aggregate_moves(self.get_done_pickings(), use_done=True)

    def get_open_move_lines(self):
        """Aggregiert geplante Move-Lines über alle offenen Lieferungen.
        Gleiche Produkte werden zusammengefasst.
        """
        return self._aggregate_moves(self.get_open_pickings(), use_done=False)

    def _aggregate_moves(self, pickings, use_done=True):
        """Interne Aggregations-Methode.
        use_done=True  → qty aus move.quantity (tatsächlich geliefert)
        use_done=False → qty aus move.product_uom_qty (geplant)
        """
        line_map = {}
        for picking in pickings:
            relevant_moves = picking.move_ids.filtered(
                lambda m: m.state == 'done' if use_done
                else m.state not in ('cancel', 'done')
            )
            for move in relevant_moves:
                pid = move.product_id.id
                if pid not in line_map:
                    line_map[pid] = {
                        'product': move.product_id,
                        'product_uom_qty': 0.0,
                        'qty_done': 0.0,
                        'uom_name': move.product_uom.name,
                        'lot_names': [],
                        'picking_names': [],
                    }
                if use_done:
                    line_map[pid]['qty_done'] += move.quantity
                    line_map[pid]['product_uom_qty'] += move.product_uom_qty
                    for ml in move.move_line_ids:
                        if ml.lot_id and ml.lot_id.name not in line_map[pid]['lot_names']:
                            line_map[pid]['lot_names'].append(ml.lot_id.name)
                else:
                    line_map[pid]['product_uom_qty'] += move.product_uom_qty
                    if picking.name not in line_map[pid]['picking_names']:
                        line_map[pid]['picking_names'].append(picking.name)
        return list(line_map.values())
