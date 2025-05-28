from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_type_client = fields.Selection(
        [
            ("supplier", "Supplier"),
            ("employee", "Employee"),
            ("customer", "Customer"),
        ],
        "client type"
    )
