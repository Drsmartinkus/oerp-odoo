from odoo import models


# TODO: copy pasted from sale_component_sticker_info_mrp_purchase. Should
# put it in common place!
def get_sale_lines_from_stock_moves(moves):
    """Get sale lines from current stock moves or its first parent moves."""
    sale_lines = moves.mapped('sale_line_id')
    if sale_lines:
        return sale_lines
    group = moves.group_id
    parent_moves = group.mrp_production_ids.move_dest_ids
    if parent_moves:
        sale_lines = parent_moves.sale_line_id
        if sale_lines:
            return sale_lines
        return get_sale_lines_from_stock_moves(parent_moves)
    return moves.env['sale.order.line']


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_procurement_values(self):
        """Extend to propagate forced supplier partner from related SO."""
        values = super()._prepare_procurement_values()
        if not values.get('supplierinfo_name'):
            sale_line = get_sale_lines_from_stock_moves(self)[:1]
            partner = sale_line.order_id.partner_supplier_id
            if partner:
                values['supplierinfo_name'] = partner
        return values
