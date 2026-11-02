from odoo import models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_confirm(self):
        # Nur für Eingänge (dein Typ: "Eingänge / Anlieferungen")
        # Du kannst hier auch explizit nach picking_type_id == 1 filtern,
        # wenn du sichergehen willst.
        incoming_pickings = self.filtered(
            lambda p: p.picking_type_code == "incoming"
        )
        res = super(StockPicking, (self - incoming_pickings)).action_confirm()
        if incoming_pickings:
            incoming_pickings._auto_set_destination_locations()
            res = super(StockPicking, incoming_pickings).action_confirm()
        return res

    def _auto_set_destination_locations(self):
        """
        Setzt für jede Move-Line den location_dest_id auf den letzten
        internen Lagerort mit Bestand des Produkts.
        """
        StockQuant = self.env["stock.quant"]
        for picking in self:
            # Optional: nur für deinen spezifischen Vorgangstyp
            # picking_type_id ist Many2one zu stock.picking.type
            # Bei dir hat "Eingänge / Anlieferungen" ID 1:
            if picking.picking_type_id.id != 1:
                continue

            for move in picking.move_ids:
                product = move.product_id
                if not product:
                    continue

                # Suche letzten internen Lagerort mit Bestand > 0
                quant = StockQuant.search(
                    [
                        ("product_id", "=", product.id),
                        ("location_id.usage", "=", "internal"),
                        ("quantity", ">", 0),
                    ],
                    order="id desc",
                    limit=1,
                )
                if quant and quant.location_id:
                    # Zielort setzen
                    move.location_dest_id = quant.location_id
                # else: Fallback = Standard-Zielort des picking.type bleibt
