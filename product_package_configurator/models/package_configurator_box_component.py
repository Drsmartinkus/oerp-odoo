from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .. import const, utils
from ..value_objects import layout as vo_layout
from ..value_objects.component import BoxComponentType


class PackageConfiguratorBoxComponentType(models.Model):
    _name = 'package.configurator.box.component'
    _description = "Package Configurator Box Component"

    @api.model
    def _get_component_type_selection(self):
        return [(ct.name, ct.label) for ct in self.get_component_types()]

    configurator_id = fields.Many2one('package.configurator.box', required=True)
    component_type = fields.Selection(
        _get_component_type_selection,
        required=True,
        default='base_greyboard',
    )
    scope = fields.Selection(const.SHEET_TYPE_SELECTION, compute='_compute_type_data')
    sheet_type_id = fields.Many2one(
        'package.sheet.type', domain="[('scope', '=', scope)]"
    )
    sheet_id = fields.Many2one(
        'package.sheet',
        required=True,
        domain="[('scope', '=', scope)]"
        # TODO: make this computed and stored!
    )
    fit_qty = fields.Integer(compute='_compute_type_data', string="Fit Quantity")

    @api.depends(
        'component_type',
        'sheet_id',
        'configurator_id.base_length',
        'configurator_id.base_width',
        'configurator_id.lid_height',
        'configurator_id.lid_extra',
        'configurator_id.outside_wrapping_extra',
    )
    def _compute_type_data(self):
        for rec in self:
            ct = rec.get_component_type()
            data = rec._get_init_type_data(ct)
            if ct.name:
                data['fit_qty'] = rec._calc_fit_qty(ct)
            rec.update(data)

    @api.onchange('component_type')
    def _onchange_component_type(self):
        if not self.component_type:
            return
        if self.sheet_type_id:
            self.sheet_type_id = False
        if self.sheet_id:
            self.sheet_id = False

    @api.constrains('component_type')
    def _check_component_type(self):
        for rec in self:
            ctypes = rec.configurator_id.component_ids.mapped('component_type')
            if len(ctypes) != len(set(ctypes)):
                raise ValidationError(
                    _("Component types must be unique per configurator!")
                )

    @api.constrains('scope', 'sheet_type_id', 'sheet_id')
    def _check_scope(self):
        for rec in self:
            scopes = {rec.scope, rec.sheet_id.scope}
            if rec.sheet_type_id:
                scopes.add(rec.sheet_type_id.scope)
            if len(scopes) != 1:
                raise ValidationError(
                    _("Scope mismatch. Scope must match between component options!")
                )

    @api.model
    def get_component_types(self) -> list[BoxComponentType]:
        return [
            # Grey board types.
            BoxComponentType(
                name='base_greyboard',
                label="Base Grey Board",
                scope=const.SheetTypeScope.GREYBOARD,
                length_field='base_layout_length',
                width_field='base_layout_width',
            ),
            BoxComponentType(
                name='lid_greyboard',
                label="Lid Grey Board",
                scope=const.SheetTypeScope.GREYBOARD,
                length_field='lid_layout_length',
                width_field='lid_layout_width',
            ),
            # Wrapping Paper types.
            BoxComponentType(
                name='base_wrappingpaper_inside',
                label="Base Inside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
                length_field='base_inside_wrapping_length',
                width_field='base_inside_wrapping_width',
            ),
            BoxComponentType(
                name='base_wrappingpaper_outside',
                label="Base Outside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
                length_field='base_outside_wrapping_length',
                width_field='base_outside_wrapping_width',
            ),
            BoxComponentType(
                name='lid_wrappingpaper_inside',
                label="Lid Inside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
                length_field='lid_inside_wrapping_length',
                width_field='lid_inside_wrapping_width',
            ),
            BoxComponentType(
                name='lid_wrappingpaper_outside',
                label="Lid Outside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
                length_field='lid_outside_wrapping_length',
                width_field='lid_outside_wrapping_width',
            ),
        ]

    def get_component_type(self) -> BoxComponentType:
        self.ensure_one()
        # Happens before record is saved.
        if not self.component_type:
            return BoxComponentType.from_default()
        component_types = self.get_component_types()
        for ct in component_types:
            # There should always be a match, because action_type selection
            # is generated from this action types list itself!
            if ct.name == self.component_type:
                return ct

    def _calc_fit_qty(self, component_type: BoxComponentType):
        def can_calc(ct, sheet):
            return (
                cfg[ct.length_field]
                and cfg[ct.width_field]
                and sheet.sheet_length
                and sheet.sheet_width
            )

        self.ensure_one()
        ct = component_type
        cfg = self.configurator_id
        sheet = self.sheet_id
        if not can_calc(ct, sheet):
            return 0
        product_layout = vo_layout.Layout2D(
            length=cfg[ct.length_field], width=cfg[ct.width_field]
        )
        sheet_layout = vo_layout.Layout2D(
            length=sheet.sheet_length, width=sheet.sheet_width
        )
        layout_fitter = vo_layout.LayoutFitter(
            product_layout=product_layout, sheet_layout=sheet_layout
        )
        return utils.fitter.calc_fit_quantity(layout_fitter)

    def _get_init_type_data(self, component_type: BoxComponentType):
        self.ensure_one()
        return {
            'scope': component_type.scope,
            'fit_qty': 0,
        }
