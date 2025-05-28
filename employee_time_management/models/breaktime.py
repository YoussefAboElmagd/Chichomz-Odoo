from odoo import fields, models, api



class BreakTime(models.Model):
    _name = 'attendance.breaktime'

    def _default_employee(self):
        return self.env.user.employee_id
    

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True, readonly=True)
    break_start = fields.Datetime(string="Break Start", readonly=True)
    break_finish = fields.Datetime(string="Break End", readonly=True)
    break_duration = fields.Float(string='Break Time', store=True, readonly=True)






# class TestDist(models.Model):
#     _inherit = 'account.analytic.distribution.model'


#     #POS Testing
#     pos_shop = fields.Many2one(
#         'pos.config',
#         string='Point Of Sale',
#         ondelete='cascade',
#         help="Select a shop for which the analytic distribution will be used (e.g. create new customer invoice or Sales order if we select this company, it will automatically take this as an analytic account)",
#     )   



# class POSA(models.Model):
#     _inherit = 'pos.order.line'

#     analytic_distribution = fields.Json(
#     ) # add the inverse function used to trigger the creation/update of the analytic lines accordingly (field originally defined in the analytic mixin)


class SaleOrderTestiiiing(models.Model):
    _inherit = 'sale.order'


    company_currency_id_sale = fields.Many2one(string='Company Currency',related='company_id.currency_id', readonly=True)

    tax_total_signed_sale = fields.Monetary(
        string='Taxes',
        compute='_compute_tax_total_tree', 
        # store=True, readonly=True,
        currency_field='company_currency_id_sale'

    )
    untaxed_amount_signed_sale = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_untaxed_amount_tree', 
        # store=True, readonly=True,
        currency_field='company_currency_id_sale'

    )
    amount_total_signed_sale = fields.Monetary(
        string='Total',
        compute='_compute_amount_tree', 
        # store=True, readonly=True,
        currency_field='company_currency_id_sale'

    )
    # store=True, readonly=True,
    def _compute_amount_tree(self):
        for order in self:
            final_total = order.currency_id.with_context(date=order.date_order).compute(order.amount_total, order.company_currency_id_sale)
            order.amount_total_signed_sale = final_total
    def _compute_untaxed_amount_tree(self):
        for order in self:
            final_total = order.currency_id.with_context(date=order.date_order).compute(order.amount_untaxed, order.company_currency_id_sale)
            order.untaxed_amount_signed_sale = final_total
    def _compute_tax_total_tree(self):
        for order in self:
            final_total = order.currency_id.with_context(date=order.date_order).compute(order.amount_tax, order.company_currency_id_sale)
            order.tax_total_signed_sale = final_total

    @api.model 
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(SaleOrderTestiiiing, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'amount_total_signed_sale' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    amount_total_signed_sale_t = 0.0
                    for record in lines:
                        amount_total_signed_sale_t += record.amount_total_signed_sale
                    line['amount_total_signed_sale'] = amount_total_signed_sale_t
        if 'tax_total_signed_sale' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    tax_total_signed_sale_t = 0.0
                    for record in lines:
                        tax_total_signed_sale_t += record.tax_total_signed_sale
                    line['tax_total_signed_sale'] = tax_total_signed_sale_t
        if 'untaxed_amount_signed_sale' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    untaxed_amount_signed_sale_t = 0.0
                    for record in lines:
                        untaxed_amount_signed_sale_t += record.untaxed_amount_signed_sale
                    line['untaxed_amount_signed_sale'] = untaxed_amount_signed_sale_t

        return res        