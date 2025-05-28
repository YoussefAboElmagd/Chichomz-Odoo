from odoo import fields, models, api
from datetime import datetime


class ContactCategory(models.Model):
    _name = "customer.contact.category"
    name = fields.Char(string="Category")

class ContactSubcategory(models.Model):
    _name = "customer.contact.subcategory"
    name = fields.Char(string="Subcategory")
  

class ContactStatus(models.Model):
    _name = "customer.contact.status"
    name = fields.Char(string="Status")
    # x_currency_id = fields.Many2one(
    #     comodel_name='res.currency', string="currency id")
class customercontacts(models.Model):
    _inherit = "res.partner"
    x_currency_id = fields.Many2one(
        comodel_name='res.currency', string="Currency Type", required=True, default=lambda self: self.env.company.currency_id)
    shipping_fees = fields.Monetary(currency_field='x_currency_id')
    termination_date = fields.Date(string="Termination Date")
    joining_date = fields.Date(
        string="Joining Date", default=fields.Date.today())
    shipping_fees = fields.Float(string="Shipping Fees")
    contract_signed = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string="Contract Signed")
    documents_shipped = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string="Documents Shipped")
    category = fields.Many2many('customer.contact.category', string="Category")
    x_subcategory_x = fields.Many2many('customer.contact.subcategory')
    x_location=fields.Char(string="Location")
    shipping_outside_cairo_fees=fields.Char(string="Shipping Outside Cairo Fees")
    status = fields.Many2one('customer.contact.status', string="Status")
    skq = fields.Char(string="Skq")
    margin = fields.Float(
        string="Margin")

    date_difference = fields.Char(
        string='Contract Duration', compute='_compute_years_difference')

    @api.onchange('termination_date', 'joining_date')
    def _compute_years_difference(self):
        for record in self:
            if record.termination_date and record.joining_date:
                y = record.termination_date.year-record.joining_date.year
                m = record.termination_date.month-record.joining_date.month

                # If the birth month is later than the current month,
                # adjust the age and months difference
                if m < 0:
                    y -= 1
                    m = 12 - abs(m)
                record.date_difference = f"{y} Years {m} Months"
            elif record.joining_date:
                # Get the current date
                today = datetime.now()

                # Calculate the difference between birth date and current date
                y = today.year - record.joining_date.year
                m = today.month - record.joining_date.month

                # If the birth month is later than the current month,
                # adjust the age and months difference
                if m < 0:
                    y -= 1
                    m = 12 - abs(m)
                record.date_difference = f"{y} Years {abs(m)} Months"
            else:
                record.date_difference = f"0 Years 0 Months"
