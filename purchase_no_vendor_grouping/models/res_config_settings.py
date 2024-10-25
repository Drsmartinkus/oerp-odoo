from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_no_vendor_grouping = fields.Boolean(
        related='company_id.purchase_no_vendor_grouping',
        readonly=False,
    )
