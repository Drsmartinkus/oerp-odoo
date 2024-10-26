from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_supplier_id = fields.Many2one('res.partner', "Forced Vendor")
