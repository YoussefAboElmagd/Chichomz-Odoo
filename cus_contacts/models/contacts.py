from odoo import fields, models



class ContactCategory(models.Model):
    _name = "customer.contact.category"
    name = fields.Char(string="Category")

class ContactStatus(models.Model):
    _name = "customer.contact.status"
    name = fields.Char(string="Status")


class customercontacts(models.Model):
    _inherit="res.partner"
    
    termination_date=fields.Date(string="Termination Date")
    joining_date=fields.Date(string="Joining Date")
    shipping_fees=fields.Float(string="Shipping Fees")
    contract_signed=fields.Selection([('yes','Yes'),('no','No')],string="Contract Signed") 
    documents_shipped=fields.Selection([('yes','Yes'),('no','No')],string="Documents Shipped") 
    category=fields.Many2many('customer.contact.category',string="Category")
    status=fields.Many2one('customer.contact.status',string="Status")
    skq=fields.Char(string="Skq")




