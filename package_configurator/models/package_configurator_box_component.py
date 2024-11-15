from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .. import const, utils
from ..value_objects import layout as vo_layout
from ..value_objects.component import BoxComponentType

LAYOUT_CFG_MANDATORY_FIELDS = [
    'base_length',
    'base_width',
    'base_height',
]


class PackageConfiguratorBoxComponent(models.Model):
    _name = 'package.configurator.box.component'
    _description = "Package Configurator Box Component"

    @api.depends('component_type')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = utils.misc.get_selection_label(rec, 'component_type')

    @api.model
    def _get_component_type_selection(self):
        return [(ct.name, ct.label) for ct in self.get_component_types()]

    configurator_id = fields.Many2one('package.configurator.box', required=True)
    component_type = fields.Selection(
        _get_component_type_selection,
        required=True,
        default='base_greyboard',
    )
    component_length = fields.Float(compute='_compute_type_data', string="Length")
    component_width = fields.Float(compute='_compute_type_data', string="Width")
    scope = fields.Selection(const.SHEET_TYPE_SELECTION, compute='_compute_type_data')
    sheet_type_id = fields.Many2one(
        'package.sheet.type', domain="[('scope', '=', scope)]"
    )
    sheet_id = fields.Many2one(
        'package.sheet',
        required=True,
        domain="[('scope', '=', scope)]",
        store=True,
        readonly=False,
        compute='_compute_sheet_id',
    )
    print_color_id = fields.Many2one('package.print.color')
    sheet_usable_length = fields.Float(compute='_compute_type_data')
    sheet_usable_width = fields.Float(compute='_compute_type_data')
    fit_qty = fields.Integer(
        compute='_compute_type_data',
        string="Fit Quantity",
        help="How many box layouts would fit on single raw sheet",
    )

    @api.depends(
        'component_type',
        'sheet_id',
        'configurator_id.base_length',
        'configurator_id.base_width',
        'configurator_id.lid_height',
        'configurator_id.lid_extra',
        'configurator_id.outside_wrapping_extra',
        'configurator_id.component_ids.component_type',
        'configurator_id.print_house_id',
    )
    def _compute_type_data(self):
        for rec in self:
            ct = rec.get_component_type()
            data = rec._get_init_type_data(ct)
            rec.update(data)
        configs = self.mapped('configurator_id')
        for cfg in configs:
            res = self.env['package.box.layout'].get_cfg_layouts(cfg)
            for ctype, layout in res.items():
                for comp in cfg.component_ids:
                    if comp.component_type != ctype:
                        continue
                    comp.update(
                        {
                            'component_length': layout.length,
                            'component_width': layout.width,
                            **comp._get_sheet_usable_dimensions_data(),
                        }
                    )
                    # NOTE. We must wait, before component_length, component_width
                    # is set as it is needed for _calc_fit_qty
                    comp.fit_qty = comp._calc_fit_qty()
                    break

    @api.depends('sheet_type_id')
    def _compute_sheet_id(self):
        for rec in self:
            if not rec.sheet_type_id:
                continue
            # We can't rely on component_length, component_width compute,
            # because this one can be computed earlier and then those
            # values would be 0, so we directly get result from get_cfg_layouts!
            res = self.env['package.box.layout'].get_cfg_layouts(rec.configurator_id)
            layout = res[rec.component_type]
            if not layout.length or not layout.width:
                continue
            rec.sheet_id = rec.env['package.sheet.match'].match(
                rec.sheet_type_id,
                vo_layout.Layout2D(length=layout.length, width=layout.width),
            )

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
        configs = self.mapped('configurator_id')
        for cfg in configs:
            ctypes = cfg.component_ids.mapped('component_type')
            if 'base_greyboard' not in ctypes:
                raise ValidationError(_("Base Greyboard component is required!"))
            if len(ctypes) != len(set(ctypes)):
                raise ValidationError(
                    _("Component types must be unique per configurator!")
                )

    @api.constrains('component_type', 'sheet_type_id', 'sheet_id')
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
            ),
            BoxComponentType(
                name='lid_greyboard',
                label="Lid Grey Board",
                scope=const.SheetTypeScope.GREYBOARD,
            ),
            # Wrapping Paper types.
            BoxComponentType(
                name='base_wrappingpaper_inside',
                label="Base Inside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
            ),
            BoxComponentType(
                name='base_wrappingpaper_outside',
                label="Base Outside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
            ),
            BoxComponentType(
                name='lid_wrappingpaper_inside',
                label="Lid Inside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
            ),
            BoxComponentType(
                name='lid_wrappingpaper_outside',
                label="Lid Outside Wrapping Paper",
                scope=const.SheetTypeScope.WRAPPINGPAPER,
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

    def _get_sheet_usable_dimensions_data(self):
        self.ensure_one()
        sheet = self.sheet_id
        house = self.configurator_id.print_house_id
        return {
            'sheet_usable_length': min(
                # If max is not set, it means, we have no limit, so we use sheet
                # length!
                sheet.sheet_length,
                house.print_max_length or sheet.sheet_length,
            ),
            'sheet_usable_width': min(
                sheet.sheet_width, house.print_max_width or sheet.sheet_width
            ),
        }

    def _calc_fit_qty(self):
        def can_calc():
            return (
                self.component_length
                and self.component_width
                and self.sheet_usable_length
                and self.sheet_usable_width
            )

        self.ensure_one()
        if not can_calc():
            return 0
        product_layout = vo_layout.Layout2D(
            length=self.component_length, width=self.component_width
        )
        sheet_layout = vo_layout.Layout2D(
            length=self.sheet_usable_length, width=self.sheet_usable_width
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
            'component_length': 0.0,
            'component_width': 0.0,
            'sheet_usable_length': 0.0,
            'sheet_usable_width': 0.0,
        }
