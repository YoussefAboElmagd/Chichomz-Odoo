from odoo import models, fields

class HelpdeskTicketSKU(models.Model):
    _name = 'helpdesk.ticket.sku'
    _description = 'Ticket SKU'
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    name = fields.Char(string="SKU", required=True , tracking=True,)
    description = fields.Text(string="Description")