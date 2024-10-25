from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestPurchaseNoVendorGrouping(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResPartner = cls.env['res.partner']
        cls.IrConfigParameter = cls.env['ir.config_parameter']
        cls.PurchaseOrder = cls.env['purchase.order']
        cls.ProductCategory = cls.env['product.category']
        cls.ProductProduct = cls.env['product.product']
        cls.ProcurementGroup = cls.env['procurement.group']
        cls.company_main = cls.env.ref('base.main_company')
        cls.category_1 = cls.env["product.category"].create({"name": "MY-CATEGORY-1"})
        cls.partner_vendor_1 = cls.env["res.partner"].create({"name": "MY-PARTNER-1"})
        cls.product_1 = cls._create_product(
            "MY-PRODUCT-1", cls.category_1, cls.partner_vendor_1
        )
        cls.product_2 = cls._create_product(
            "MY-PRODUCT-2", cls.category_1, cls.partner_vendor_1
        )
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.stock_location_route = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.stock_rule = cls.stock_location_route.rule_ids[0]
        cls.values = {
            "company_id": cls.company_main,
            "date_planned": fields.Datetime.now(),
        }
        cls.company_main.purchase_no_vendor_grouping = True

    @classmethod
    def _create_product(cls, name, category, partner):
        product = cls.ProductProduct.create(
            {
                "name": name,
                "type": "product",
                "categ_id": category.id,
                "seller_ids": [(0, 0, {"partner_id": partner.id, "min_qty": 1.0})],
            }
        )
        return product

    def run_procurement(self, products, origin, values):
        procure_items = []
        for product in products:
            procurement = self.ProcurementGroup.Procurement(
                product,
                1,
                product.uom_id,
                self.location_stock,
                False,
                origin,
                self.env.company,
                values,
            )
            rule = self.ProcurementGroup._get_rule(
                procurement.product_id, procurement.location_id, procurement.values
            )
            procure_items.append((procurement, rule))
        self.stock_rule._run_buy(procure_items)

    def test_01_purchase_no_vendor_grouping_multi_run_buy(self):
        # WHEN
        self.run_procurement(
            self.product_1 | self.product_2,
            "MY-ORIGIN-1",
            {
                "company_id": self.company_main,
                "date_planned": fields.Datetime.now(),
            },
        )
        self.run_procurement(
            self.product_1 | self.product_2,
            "MY-ORIGIN-2",
            {
                "company_id": self.company_main,
                "date_planned": fields.Datetime.now(),
            },
        )
        # THEN
        purchases = self.PurchaseOrder.search(
            [('partner_id', '=', self.partner_vendor_1.id)]
        )
        self.assertEqual(len(purchases), 2)

    def test_02_purchase_no_vendor_grouping_disabled_multi_run_buy(self):
        # GIVEN
        self.company_main.purchase_no_vendor_grouping = False
        # WHEN
        self.run_procurement(
            self.product_1 | self.product_2,
            "MY-ORIGIN-1",
            {
                "company_id": self.company_main,
                "date_planned": fields.Datetime.now(),
            },
        )
        self.run_procurement(
            self.product_1 | self.product_2,
            "MY-ORIGIN-2",
            {
                "company_id": self.company_main,
                "date_planned": fields.Datetime.now(),
            },
        )
        # THEN
        purchases = self.PurchaseOrder.search(
            [('partner_id', '=', self.partner_vendor_1.id)]
        )
        self.assertEqual(len(purchases), 1)
