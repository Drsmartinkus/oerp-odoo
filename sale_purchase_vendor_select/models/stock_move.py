from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_procurement_values(self):
        """Extend to propagate forced supplier partner."""
        values = super()._prepare_procurement_values()
        if not values.get('supplierinfo_name'):
            partner = self.sale_line_id.order_id.partner_supplier_id
            if partner:
                values['supplierinfo_name'] = partner
        return values
