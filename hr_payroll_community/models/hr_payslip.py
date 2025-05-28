# -*- coding:utf-8 -*-

import babel
from collections import defaultdict
from datetime import date, datetime, time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from pytz import utc

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils

# This will generate 16th of days
ROUNDING_FACTOR = 16




class HrContractAbsence(models.Model):
   
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    
    x_today_wage = fields.Float(string='Today Wage')
    x_absence = fields.Float(string='Absence', store=True , compute="_compute_x_absence")
    x_penalties = fields.Float(string='Penalties' , store=True , compute="_compute_x_penalties")
    x_delay = fields.Float(string='Delay', compute="_compute_x_delay")
    x_total_salary = fields.Float(string='Total Salary', compute="_compute_x_total_salary" , store = True)
    x_other_discounts = fields.Float(string='Other Deductions' , readonly = True)
    x_number_of_absence_days = fields.Float(string='Number Of Absence Days' , store = True)
    x_number_of_penalty_days = fields.Float(string='Number Of Penalty Days')
    x_number_of_hours = fields.Float(string='Number Of Hours')
    x_hour_rate = fields.Float(string='Hour Rate')
    x_overtime_hour = fields.Float(string='Overtime Hour')
    x_number_of_overtime_days = fields.Float(string='Number Of Overtime Days')
    x_total_overtime = fields.Float(string='Total Overtime', compute="_compute_x_total_overtime")
    x_number_of_overtime_hours = fields.Float(string='Number Of late Hours')
    x_total_discounts = fields.Float(string='Total Discounts', compute="_compute_x_total_discounts")
    x_extra_total = fields.Float(string='Extra Total', compute="_compute_x_extra_total")

    hra = fields.Monetary(string='HRA', tracking=True, 
                          help="House rent allowance.")
    other_allowance = fields.Monetary(string="Other Allowance", 
                                      help="Other allowances")
    wage = fields.Monetary('Wage', required=True, tracking=True,  help="Employee's monthly gross wage.", group_operator="avg")

    @api.depends("x_total_overtime","commission","travel_allowance","da","meal_allowance","medical_allowance","other_allowance")
    def _compute_x_extra_total(self):
        for record in self:
            record.x_extra_total = record.x_total_overtime + record.commission + record.travel_allowance + record.da + record.meal_allowance + record.medical_allowance + record.other_allowance
        
    @api.depends("x_absence","x_penalties","x_delay","x_other_discounts")
    def _compute_x_total_discounts(self):
        for record in self:
            record.x_total_discounts = record.x_absence + record.x_penalties + record.x_delay + record.x_other_discounts
        

    @api.depends("x_overtime_hour","x_number_of_overtime_hours")
    def _compute_x_total_overtime(self):
        for record in self:
            if record.x_overtime_hour:
                record.x_total_overtime = (record.x_number_of_overtime_hours + (record.x_overtime_number_of_days*8)) * record.x_overtime_hour
            else:
                record.x_total_overtime = 0.0
                
                
    
                
                
                


    @api.depends("wage","hra","commission","da","travel_allowance","meal_allowance","medical_allowance","other_allowance")
    def _compute_x_total_salary(self):
        for record in self:
                    
                    record.x_total_salary = record.wage + record.hra + record.commission + record.da + record.travel_allowance + record.meal_allowance + record.medical_allowance + record.other_allowance
               
    @api.depends("x_absence","x_number_of_absence_days")
    def _compute_x_absence(self):
        for record in self:
            if record.x_today_wage:
                if record.x_number_of_absence_days:
                    record.x_absence = record.x_number_of_absence_days * record.x_today_wage
                else:
                    record.x_absence = 0.0
            else:
                record.x_absence = 0.0
                
    @api.depends("x_penalties","x_number_of_penalty_days") 
    def _compute_x_penalties(self):
        for record in self:
            if record.x_today_wage:
                if record.x_number_of_penalty_days:
                    record.x_penalties = record.x_number_of_penalty_days * record.x_today_wage
                else:
                    record.x_penalties = 0.0
            else:
                record.x_penalties = 0.0

    @api.depends("x_delay","x_number_of_hours","x_hour_rate")
    def _compute_x_delay(self):
        for record in self:
            if record.x_hour_rate:
                if record.x_number_of_hours:
                    record.x_delay = record.x_number_of_hours * record.x_hour_rate
                else:
                    record.x_delay = 0.0
            else:
                record.x_delay = 0.0





class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _description = 'Pay Slip'

    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True,
                                states={'draft': [('readonly', False)]},
                                help='Defines the rules that have to be applied to this payslip, accordingly '
                                     'to the contract chosen. If you let empty the field contract, this field isn\'t '
                                     'mandatory anymore and thus the rules applied will be all the rules set on the '
                                     'structure of all contracts of the employee valid for the chosen period')
    name = fields.Char(string='Payslip Name', readonly=True,
                       states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, copy=False,
                         help="References",
                         states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, readonly=True, help="Employee",
                                  states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', required=True,
                            help="Start date for Payslip",
                            default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=-1, day=1,
                                                              days=0)).date()))
    date_to = fields.Date(string='Date To', required=True,
                          help="End date for Payslip",
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=0, day=1,
                                                              days=-1)).date()),
                          states={'draft': [('readonly', False)]})
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't) and 5 exist ('confirm' seems to have existed)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    line_ids = fields.One2many('hr.payslip.line', 'slip_id',
                               string='Payslip Lines', readonly=True,
                               states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 copy=False, help="Company",
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get(),
                                 states={'draft': [('readonly', False)]})
    worked_days_line_ids = fields.One2many('hr.payslip.worked_days',
                                           'payslip_id',
                                           string='Payslip Worked Days',
                                           copy=True, readonly=True,
                                           help="Payslip worked days",
                                           states={
                                               'draft': [('readonly', False)]})
    input_line_ids = fields.One2many('hr.payslip.input', 'payslip_id',
                                     string='Payslip Inputs',
                                     readonly=True,
                                     states={'draft': [('readonly', False)]})
    paid = fields.Boolean(string='Made Payment Order ? ', readonly=True,
                          copy=False,
                          states={'draft': [('readonly', False)]})
    note = fields.Text(string='Internal Note', readonly=True,
                       states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  readonly=True, help="Contract",
                                  states={'draft': [('readonly', False)]})
    details_by_salary_rule_category = fields.One2many('hr.payslip.line',
                                                      compute='_compute_details_by_salary_rule_category',
                                                      string='Details by Salary Rule Category',
                                                      help="Details from the salary rule category")
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="Indicates this payslip has a refund of another")
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches',
                                     readonly=True,
                                     copy=False,
                                     states={'draft': [('readonly', False)]})
    payslip_count = fields.Integer(compute='_compute_payslip_count',
                                   string="Payslip Computation Details")
    payslip_net = fields.Float(string="Net Salary", currency_field = "company_currency_id")
    payslip_loan = fields.Float(string="Loan", currency_field = "company_currency_id")
    payslip_gross = fields.Float(string="Gross", currency_field = "company_currency_id")

    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True,
    )
    x_department = fields.Many2one('hr.department',string='Department', related="contract_id.department_id" , readonly = False)
    x_job = fields.Many2one('hr.job',string='Job', related="contract_id.job_id" , readonly = False)
    o_wage = fields.Monetary(string='Wage' , currency_field = "company_currency_id",related="contract_id.wage" , readonly = False)
    o_other_allowance = fields.Monetary(string='Other Allowance' , currency_field = "company_currency_id", compute ="_compute_other_allowance" , readonly = False)
    o_hra = fields.Monetary(string='Hra' , currency_field = "company_currency_id",compute ="_compute_hra_count" , store = True , readonly = False )
    x_total_salary = fields.Float(string='Total Salary', related="contract_id.x_total_salary" , store = True , readonly = False)
    x_total = fields.Float(string='Total', related="line_ids.total" , readonly = False)
    beneficiary_address_1 = fields.Text(string='Beneficiary Address 1')
    beneficiary_address_2 = fields.Text(string='Beneficiary Address 2')
    beneficiary_address_3 = fields.Text(string='Beneficiary Address 3')
    # beneficiar_bank = fields.Text(string='Beneficiary Bank')

    # x_absence = fields.Float(string='Absence', related="contract_id.x_absence" , store = True)
    # x_penalties = fields.Float(string='Penalties', related="contract_id.x_penalties", store = True)
    # x_delay = fields.Float(string='Delay', related="contract_id.x_delay")
    # x_other_discounts = fields.Float(string='Other Discounts', readonly = False)
    # x_number_of_absence_days = fields.Float(string='Number Of Absence Days',  related="contract_id.x_number_of_absence_days" , readonly = False)
    # x_number_of_penalty_days = fields.Float(string='Number Of Penalty Days', related="contract_id.x_number_of_penalty_days", readonly = False)
    # x_number_of_hours = fields.Float(string='Number Of Delay Hours', related="contract_id.x_number_of_hours", readonly = False)
    # x_hour_rate = fields.Float(string='Hour Rate', related="contract_id.x_hour_rate", readonly = False)
    # x_number_of_overtime_hours = fields.Float(string='Number Of Overtime Hours', related="contract_id.x_number_of_overtime_hours", readonly = False)
    # x_number_of_overtime_days = fields.Float(string='Number Of Overtime Days', related="contract_id.x_number_of_overtime_days", readonly = False)
    # x_total_overtime = fields.Float(string='Total Overtime', related="contract_id.x_total_overtime", readonly = True)



    x_absence = fields.Monetary(string='Absence', currency_field = "company_currency_id")
    x_penalties = fields.Monetary(string='Penalties', currency_field = "company_currency_id")
    x_delay = fields.Monetary(string='Delay', currency_field = "company_currency_id")
    x_other_discounts = fields.Monetary(string='Other Deductions', currency_field = "company_currency_id")
    x_number_of_absence_days = fields.Float(string='Number Of Absence Days')
    x_number_of_penalty_days = fields.Float(string='Number Of Penalty Days')
    x_number_of_hours = fields.Float(string='Number Of Delay Hours')
    x_hour_rate = fields.Monetary(string='اجر الساعه',currency_field = "company_currency_id", compute="_compute_x_hour_rate")
    x_number_of_overtime_hours = fields.Float(string='Number Of Overtime Hours')
    x_number_of_overtime_days = fields.Float(string='Number Of Overtime Days')
    x_total_overtime_hours = fields.Monetary(string='Total Overtime Hours', currency_field = "company_currency_id", readonly = True)
    x_total_overtime_days = fields.Monetary(string='Total Overtime Days', currency_field = "company_currency_id", readonly = True)
    x_total_overtime = fields.Monetary(string='Total Overtime', currency_field = "company_currency_id", readonly = True)

    # y_absence = fields.Float(string='Absence', readonly = True)
    # y_penalties = fields.Float(string='Penalties', readonly = True)
    # y_delay = fields.Float(string='Delay', readonly = True)
    # y_other_discounts = fields.Float(string='Other Discounts', readonly = True)
    # y_number_of_absence_days = fields.Float(string='Number Of Absence Days', readonly = True)
    # y_number_of_penalty_days = fields.Float(string='Number Of Penalty Days', readonly = True)
    # y_number_of_hours = fields.Float(string='Number Of Hours', readonly = True)
    # y_hour_rate = fields.Float(string='Hour Rate', readonly = True)
    # y_number_of_overtime_hours = fields.Float(string='Number Of Overtime Hours', readonly = True)
    # y_total_overtime = fields.Float(string='Total Overtime', readonly = True)
    is_cleared = fields.Boolean(string='Is Cleared' , default= False)



    @api.onchange('x_other_discounts')
    def onchange_other_discounts(self):
        for rec in self:
            if rec.contract_id :
               rec.contract_id.x_other_discounts = rec.x_other_discounts 
            else:
                rec.x_other_discounts = 0.0

    def _compute_other_allowance(self):
        for rec in self:
            if rec.contract_id :
                rec.o_other_allowance = rec.contract_id.other_allowance
            else:
                rec.o_other_allowance = 0.0
    
   
    def _compute_hra_count(self):
        for rec in self:
            if rec.contract_id :
                rec.o_hra = rec.contract_id.hra
            else:
                rec.o_hra = 0.0
                
    def clear_butoon(self):
       slips = self.env["hr.payslip"].search([])
       for slip in slips:
        if slip.is_cleared == False :
            slip.y_absence = slip.x_absence 
            slip.y_penalties = slip.x_penalties
            slip.y_delay = slip.x_delay
            slip.y_other_discounts = slip.x_other_discounts
            slip.y_number_of_absence_days = slip.x_number_of_absence_days
            slip.y_number_of_penalty_days = slip.x_number_of_penalty_days
            slip.y_number_of_hours = slip.x_number_of_hours
            slip.y_hour_rate = slip.x_hour_rate
            slip.y_number_of_overtime_hours = slip.x_number_of_overtime_hours
            slip.y_total_overtime = slip.x_total_overtime
            slip.is_cleared = True
       contracts = self.env["hr.contract"].search([])
       for contract in contracts:
            contract.x_number_of_absence_days = 0
            contract.x_number_of_penalty_days = 0
            contract.x_number_of_hours = 0
            contract.x_number_of_overtime_hours = 0
            contract.x_other_discounts = 0



    def action_send_email(self):
        res = self.env.user.has_group(
            'hr_payroll_community.group_hr_payroll_community_manager')
        if res:
            email_values = {
                'email_from': self.env.user.work_email,
                'email_to': self.employee_id.work_email,
                'subject': self.name
            }
            mail_template = self.env.ref(
                'hr_payroll_community.payslip_email_template').sudo()

            mail_template.send_mail(self.id, force_send=True,
                                    email_values=email_values)

    def _compute_details_by_salary_rule_category(self):
        for payslip in self:
            payslip.details_by_salary_rule_category = payslip.mapped(
                'line_ids').filtered(lambda line: line.category_id)

    def _compute_payslip_count(self):
        for payslip in self:
            payslip.payslip_count = len(payslip.line_ids)
            
    def _compute_payslip_nets(self):
        for payslip in self:
            payslip.payslip_net = 0.0
            for line in payslip.line_ids:
                if line.code == 'NET':		
                        payslip.payslip_net = line.total
                        
    def _compute_payslip_loan(self):
        for payslip in self:
            payslip.payslip_loan = 0.0
            for line in payslip.line_ids:
                if line.code == 'LO':		
                        payslip.payslip_loan = line.total
    def _compute_payslip_gross(self):
        for payslip in self:
            payslip.payslip_gross = 0.0
            for line in payslip.line_ids:
                if line.code == 'GROSS':		
                        payslip.payslip_gross = line.total
        

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):

        if any(self.filtered(
                lambda payslip: payslip.date_from > payslip.date_to)):
            raise ValidationError(
                _("Payslip 'Date From' must be earlier 'Date To'."))

    def action_payslip_draft(self):
        return self.write({'state': 'draft'})

    def action_payslip_done(self):
        self.compute_sheet()
        return self.write({'state': 'done'})

    def action_payslip_cancel(self):
        return self.write({'state': 'cancel'})

    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy(
                {'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_done()
        formview_ref = self.env.ref('hr_payroll_community.view_hr_payslip_form',
                                    False)
        treeview_ref = self.env.ref('hr_payroll_community.view_hr_payslip_tree',
                                    False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    def check_done(self):

        return True

    def unlink(self):

        if any(self.filtered(
                lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(
                _('You cannot delete a payslip which is not draft or cancelled!'))
        return super(HrPayslip, self).unlink()

    # TODO move this function into hr_contract module, on hr.employee object
    @api.model
    def get_contract(self, employee, date_from, date_to):

        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id),
                        ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code(
                'salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            total_overtime_hours = payslip.x_number_of_overtime_hours * payslip.contract_id.x_overtime_hour
            total_overtime_days = payslip.x_number_of_overtime_days * payslip.contract_id.x_overtime_hour * 8
            total_overtime = total_overtime_hours + total_overtime_days
            absence = payslip.x_number_of_absence_days * payslip.contract_id.x_today_wage
            penalties = payslip.x_number_of_penalty_days * payslip.contract_id.x_today_wage
            delay = payslip.x_number_of_hours * payslip.contract_id.x_hour_rate
            total_salary = payslip.contract_id.wage + payslip.contract_id.hra + payslip.contract_id.commission + payslip.contract_id.da + payslip.contract_id.travel_allowance + payslip.contract_id.meal_allowance + payslip.contract_id.medical_allowance + payslip.contract_id.other_allowance
            payslip.write({'x_total_overtime_hours': total_overtime_hours, 'x_total_overtime_days': total_overtime_days, 'x_total_overtime': total_overtime, 'x_absence': absence,'x_total_salary': total_salary,'x_penalties': penalties,'x_delay': delay, 'o_wage': payslip.contract_id.wage,'o_hra': payslip.contract_id.hra,'o_other_allowance': payslip.contract_id.other_allowance})
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id,
                                             payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in
                     self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
            net_s = 0.0
            gross_s = 0.0
            loan = 0.0
            for line in self.line_ids:
                if line.code == 'NET':		
                        net_s = line.total
                elif line.code == 'GROSS':
                        gross_s = line.total
                elif line.code == 'LO':
                        loan = -line.total
            payslip.write({'payslip_net': net_s,'payslip_gross': gross_s,'payslip_loan': loan})
        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):

        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)

            # compute leave days
            leaves = {}

            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from,
                                                                   day_to,
                                                                   calendar=contract.resource_calendar_id)
            multi_leaves = []
            for day, hours, leave in day_leave_intervals:
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if len(leave) > 1:
                    for each in leave:
                        if each.holiday_id:
                            multi_leaves.append(each.holiday_id)
                else:
                    holiday = leave.holiday_id
                    current_leave_struct = leaves.setdefault(
                        holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name or _(
                                'Global Leaves'),
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code or 'GLOBAL',
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                        })
                    current_leave_struct['number_of_hours'] += hours
                    if work_hours:
                        current_leave_struct[
                            'number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from,
                                                                day_to,
                                                                calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }
            res.append(attendances)

            uniq_leaves = [*set(multi_leaves)]
            c_leaves = {}
            for rec in uniq_leaves:
                c_leaves.setdefault(rec.holiday_status_id,
                                    {'hours': float(
                                        rec.duration_display.replace(
                                            "hours",
                                            "")), })
            flag = 1
            for item in c_leaves:
                if not leaves:
                    data = {
                        'name': item.name,
                        'sequence': 20,
                        'code': item.code or 'LEAVES',
                        'number_of_hours': c_leaves[item]['hours'],
                        'number_of_days': c_leaves[item][
                                              'hours'] / work_hours,
                        'contract_id': contract.id,
                    }
                    res.append(data)

                for time_off in leaves:
                    if item == time_off:
                        leaves[item]['number_of_hours'] += c_leaves[item][
                            'hours']
                        leaves[item]['number_of_days'] += c_leaves[item][
                                                              'hours'] / work_hours
                    if item not in leaves and flag == 1:
                        data = {
                            'name': item.name,
                            'sequence': 20,
                            'code': holiday.holiday_status_id.code or 'GLOBAL',
                            'number_of_hours': c_leaves[item]['hours'],
                            'number_of_days': c_leaves[item][
                                                  'hours'] / work_hours,
                            'contract_id': contract.id,
                        }
                        res.append(data)
                        flag = 0

            res.extend(leaves.values())
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):

        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped(
            'input_ids')

        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                }
                res += [input_data]
        return res

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      amount)
            localdict['categories'].dict[category.code] = category.code in \
                                                          localdict[
                                                              'categories'].dict and \
                                                          localdict[
                                                              'categories'].dict[
                                                              category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(
                set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee,
                             contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(
                        localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict,
                                                          rule.category_id,
                                                          tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in
                                  rule._recursive_search_of_rules()]

        return list(result_dict.values())

    # YTI TODO To rename. This method is not really an onchange, as it is not in any view
    # employee_id and contract_id could be browse records
    def onchange_employee_id(self, date_from, date_to, employee_id=False,
                             contract_id=False):
        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in
                                         self.worked_days_line_ids.ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (
                employee.name, tools.ustr(
                    babel.dates.format_date(date=ttyme, format='MMMM-y',
                                            locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(
                babel.dates.format_date(date=ttyme, format='MMMM-y',
                                        locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                self.worked_days_line_ids = False
                self.contract_id = False
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            self.worked_days_line_ids = False
            return
        self.struct_id = self.contract_id.struct_id
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        if input_line_ids:
            for r in input_line_ids:
                input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return

    @api.onchange('contract_id')
    def onchange_contract(self):

        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True).onchange_employee()
        return

    def get_salary_line_total(self, code):

        self.ensure_one()
        line = self.line_ids.filtered(lambda line: line.code == code)
        if line:
            return line[0].total
        else:
            return 0.0
        
    @api.onchange('date_from')
    def onchange_date_from(self):
        """Function for getting contract for employee"""
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        if input_line_ids:
            for r in input_line_ids:
                input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        if self.line_ids.search([('name', '=', 'Meal Voucher')]):
            self.line_ids.search(
                [('name', '=', 'Meal Voucher')]).salary_rule_id.write(
                {'quantity': self.worked_days_line_ids.number_of_days})
        return

    @api.onchange('date_to')
    def onchange_date_to(self):
        """Function for getting contract for employee"""
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        if input_line_ids:
            for r in input_line_ids:
                input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        if self.line_ids.search([('name', '=', 'Meal Voucher')]):
            self.line_ids.search(
                [('name', '=', 'Meal Voucher')]).salary_rule_id.write(
                {'quantity': self.worked_days_line_ids.number_of_days})
        return

class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    slip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True,
                              ondelete='cascade', help="Payslip")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule',
                                     required=True, help="salary rule")
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Employee")
    # category_id = fields.Many2one(related='salary_rule_id.category_id', string='Category', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  required=True, index=True, help="Contract")
    rate = fields.Float(string='Rate (%)',
                        digits=dp.get_precision('Payroll Rate'), default=100.0)
    amount = fields.Float(digits=dp.get_precision('Payroll'))
    quantity = fields.Float(digits=dp.get_precision('Payroll'), default=1.0)
    total = fields.Float(compute='_compute_total', string='Total', help="Total",
                         digits=dp.get_precision('Payroll'), store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):

        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.model_create_multi
    def create(self, vals_list):

        for values in vals_list:
            if 'employee_id' not in values or 'contract_id' not in values:
                payslip = self.env['hr.payslip'].browse(values.get('slip_id'))
                values['employee_id'] = values.get(
                    'employee_id') or payslip.employee_id.id
                values['contract_id'] = values.get(
                    'contract_id') or payslip.contract_id and payslip.contract_id.id
                if not values['contract_id']:
                    raise UserError(
                        _('You must set a contract to create a payslip line.'))
        return super(HrPayslipLine, self).create(vals_list)


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True,
                                 ondelete='cascade', index=True, help="Payslip")
    sequence = fields.Integer(required=True, index=True, default=10,
                              help="Sequence")
    code = fields.Char(required=True,
                       help="The code that can be used in the salary rules")
    number_of_days = fields.Float(string='Number of Days',
                                  help="Number of days worked")
    number_of_hours = fields.Float(string='Number of Hours',
                                   help="Number of hours worked")
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  required=True,
                                  help="The contract for which applied this input")


class HrPayslipInput(models.Model):
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True,
                                 ondelete='cascade', help="Payslip", index=True)
    sequence = fields.Integer(required=True, index=True, default=10,
                              help="Sequence")
    code = fields.Char(required=True,
                       help="The code that can be used in the salary rules")
    amount = fields.Float(
        help="It is used in computation. For e.g. A rule for sales having "
             "1% commission of basic salary for per product can defined in expression "
             "like result = inputs.SALEURO.amount * contract.wage*0.01.")
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  required=True,
                                  help="The contract for which applied this input")


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(required=True, readonly=True,
                       states={'draft': [('readonly', False)]})
    slip_ids = fields.One2many('hr.payslip', 'payslip_run_id',
                               string='Payslips', readonly=True,
                               states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             help="start date",
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(
                                 date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           help="End date",
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1,
                                                               days=-1)).date()))
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="If its checked, indicates that all "
                                      "payslips generated from here are refund "
                                      "payslips.")
    is_validate = fields.Boolean(compute='_compute_is_validate')

    @api.onchange('date_start', 'date_end')
    def onchange_date_for_all(self):
            
        for payslip in self.slip_ids:
                payslip.write({'date_from': self.date_start, 'date_to': self.date_end})
                
    def draft_payslip_run(self):
        return self.write({'state': 'draft'})

    def close_payslip_run(self):
        return self.write({'state': 'close'})

    def action_validate_payslips(self):
        if self.slip_ids:
            for slip in self.slip_ids.filtered(
                    lambda slip: slip.state == 'draft'):
                slip.action_payslip_done()

    def _compute_is_validate(self):
        for record in self:
            if record.slip_ids and record.slip_ids.filtered(
                    lambda slip: slip.state == 'draft'):
                record.is_validate = True
            else:
                record.is_validate = False


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def get_work_days_data(self, from_datetime, to_datetime,
                           compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full,
                                                         resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime,
                                                       to_datetime, resource,
                                                       domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime,
                                                             to_datetime,
                                                             resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[
                day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }
