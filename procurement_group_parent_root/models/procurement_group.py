from odoo import api, fields, models
from odoo.tools.sql import column_exists, create_column


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    parent_root_id = fields.Many2one(
        'procurement.group',
        compute='_compute_parent_root_id',
        store=True,
        recursive=True,
    )

    @api.depends('stock_move_ids.move_dest_ids.group_id')
    def _compute_parent_root_id(self):
        for rec in self:
            rec.parent_root_id = rec._get_parent_root()

    def _get_parent_root(self):
        def get_parent(g):
            # Usually should be a single group, but either way using first found!..
            return g.stock_move_ids.move_dest_ids.group_id[:1]

        self.ensure_one()
        parent_group = self
        candidate = get_parent(parent_group)
        while candidate:
            parent_group = candidate
            candidate = get_parent(parent_group)
        return parent_group

    def _auto_init(self):
        # To avoid computing old procurement groups. Depending on database there could
        # be huge number of rows in this table!
        if not column_exists(self.env.cr, "procurement_group", "parent_root_id"):
            create_column(self.env.cr, "procurement_group", "parent_root_id", "int4")
        return super()._auto_init()
