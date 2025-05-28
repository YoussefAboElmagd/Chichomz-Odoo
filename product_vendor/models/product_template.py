from odoo import fields, models, api

class ProductProduct(models.Model):

    _inherit = "product.product"
    vendor = fields.Many2one("res.partner",string='Vendor')


class accountmoveline(models.Model):
    _inherit = "account.move.line"
    vendor= fields.Many2one(
        'res.partner',
        string='Vendor'

    )
class saleorderline(models.Model):
    _inherit = "sale.order.line"
    vendor= fields.Many2one(
        'res.partner',
        string='Vendor'

    )
