from collections import defaultdict

from odoo import api, fields, models

from .. import const
from ..value_objects import sheet as vo_sheet


class PackageConfiguratorBoxCirculationItem(models.Model):
    _name = 'package.configurator.box.circulation.item'
    _description = "Package Configurator Box Circulation Component"

    circulation_id = fields.Many2one(
        'package.configurator.box.circulation',
        required=True,
        ondelete='cascade',
    )
    component_id = fields.Many2one(
        'package.configurator.box.component',
        required=True,
        ondelete='cascade',
    )
    quantity = fields.Integer(compute='_compute_quantity', help="Raw Sheets Quantity")
    print_unit_cost = fields.Float(
        digits=const.DecimalPrecision.COST,
        compute='_compute_print_unit_cost',
    )
    circulation_setup_ids = fields.One2many(
        'package.configurator.box.circulation.item.setup',
        'circulation_item_id',
    )

    @api.depends(
        'circulation_id.configurator_id.component_ids.component_type',
        'circulation_id.configurator_id.component_ids.sheet_id',
        'circulation_id.configurator_id.component_ids.fit_qty',
        'circulation_id.quantity',
    )
    def _compute_quantity(self):
        circulations = self.mapped('circulation_id')
        for circ in circulations:
            data = self._get_quantity_data(circ)
            for circ_comp, qty in data.items():
                circ_comp.quantity = qty

    @api.depends(
        'circulation_id.configurator_id.component_ids.sheet_id',
        'circulation_id.configurator_id.component_ids.print_color_id',
        'circulation_id.quantity',
        'quantity',
    )
    def _compute_print_unit_cost(self):
        circulations = self.mapped('circulation_id')
        for circ in circulations:
            data = self._get_print_unit_cost_data(circ)
            for circ_comp, unit_cost in data.items():
                circ_comp.print_unit_cost = unit_cost

    def action_open_circulation_setups(self):
        self.ensure_one()
        action = (
            self.env['ir.actions.act_window']
            .sudo()
            ._for_xml_id(
                'package_configurator.'
                + 'package_configurator_box_circulation_item_setup_action'
            )
        )
        action.update(
            {
                'context': {'default_circulation_item_id': self.id},
                'domain': [('circulation_item_id', '=', self.id)],
            }
        )
        return action

    def _get_quantity_data(self, circ):
        data = self._get_init_quantity_data(circ)
        circ_items = circ.item_ids
        qty_map = defaultdict(list)
        for item in circ_items:
            component = item.component_id
            if not component.fit_qty:
                continue
            sheet = component.sheet_id
            # min_qty of course is the same, but using it to later
            # retrieve it when building SheetQuantity!
            qty_map[(sheet.id, sheet.min_qty)].append(
                vo_sheet.SheetQuantityItem(
                    # Mapping by circ_item record!
                    code=item,
                    fit_qty=component.fit_qty,
                    setup_raw_qty=sum(
                        s.setup_raw_qty for s in item.circulation_setup_ids
                    ),
                )
            )
        sheets = []
        for (__, min_qty), items in qty_map.items():
            sheets.append(vo_sheet.SheetQuantity(min_qty=min_qty, items=items))
        data.update(self.env['package.sheet.quantity'].calc(circ.quantity, sheets))
        return data

    def _get_init_quantity_data(self, circ):
        return {ci: 0 for ci in circ.item_ids}

    def _get_print_unit_cost_data(self, circ):
        data = self._get_init_print_unit_cost_data(circ)
        pricelist = circ.configurator_id.print_house_id.print_pricelist_id
        if not pricelist:
            return data
        circ_items = circ.item_ids
        sheet_color_map = defaultdict(lambda: self.browse())
        for item in circ_items:
            component = item.component_id
            color = component.print_color_id
            if not color:
                continue
            # Grouping by sheet/color to be able to use total quantity
            # of grouped items. This way cost is more optimized as
            # we don't isolate each component cost if same material
            # and color would be used for multiple components!
            sheet_color_map[(item.component_id.sheet_id, color)] |= item
        for (_sheet, color), items in sheet_color_map.items():
            quantity = sum(item.quantity for item in items)
            unit_cost = pricelist.match_rule(color, quantity).unit_cost
            data.update({item: unit_cost for item in items})
        return data

    def _get_init_print_unit_cost_data(self, circ):
        return {ci: 0.0 for ci in circ.item_ids}
