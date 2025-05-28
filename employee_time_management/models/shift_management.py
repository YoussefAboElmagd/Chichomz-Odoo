from odoo import fields,models
from datetime import datetime

class ShiftManagement(models.Model):
    _name = 'attendance.shift.management'

    def _default_employee(self):
        return self.env.user.employee_id
    
    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True, readonly=True)
    date = fields.Date(string='Date',default=datetime.today())
    total_work = fields.Float(string='Total Work', compute='_compute_total_work', default=0.0)
    total_break = fields.Float(string='Total Breaks', compute='_compute_total_break', default=0.0)
    total_idle = fields.Float(string='Total Idle', compute='_compute_total_idle', default=0.0)
    lost_hours = fields.Float(string='Lost Hours', compute='_compute_lost_hours', default=0.0)
    actual_work = fields.Float(string='Actual Work', compute='_compute_actual_work', default=0.0)


    def _compute_total_work(self):
        # total_work_records = self.env['hr.attendance'].search([])
        # if total_work_records:
        #     shift_date = self.date.strftime('%Y-%m-%d')
        #     for record in total_work_records:
        #         rec_date = record.check_in.strftime('%Y-%m-%d')
        #         if (shift_date == rec_date):
        #             self.total_work = self.total_work + (record.worked_hours * 60)
        #         else:
        #             self.total_work = 0.0
        # else:
        #     self.total_work = 0.0                
        total_work_records = self.env['hr.attendance'].search([])
        if total_work_records:
            for rec in self:
                shift_date = rec.date.strftime('%Y-%m-%d')
                for record in total_work_records:
                    rec_date = record.check_in.strftime('%Y-%m-%d')
                    if (shift_date == rec_date) and (rec.employee_id.id == record.employee_id.id):
                        rec.total_work = rec.total_work + (record.worked_hours * 60)
                if rec.total_work == 0:
                    rec.total_work = 0    
        else:
            for rec in self:
                rec.total_work = 0  
          

    def _compute_total_break(self):
     
        total_work_records = self.env['attendance.breaktime'].search([])
        if total_work_records:
            for rec in self:
                shift_date = rec.date.strftime('%Y-%m-%d')
                for record in total_work_records:
                    rec_date = record.break_start.strftime('%Y-%m-%d')
                    if (shift_date == rec_date) and (rec.employee_id.id == record.employee_id.id):
                        rec.total_break = rec.total_break + record.break_duration
                if rec.total_break == 0:
                    rec.total_break = 0  
        else:
            for rec in self:
                rec.total_break = 0  


    def _compute_total_idle(self):
        total_work_records = self.env['attendance.idle.time'].search([])
        if total_work_records:
            for rec in self:
                shift_date = rec.date.strftime('%Y-%m-%d')
                for record in total_work_records:
                    if record.idle_start:
                        rec_date = record.idle_start.strftime('%Y-%m-%d')
                        if (shift_date == rec_date) and (rec.employee_id.id == record.employee_id.id):
                            rec.total_idle = rec.total_idle + record.idle_duration
                if rec.total_idle == 0:
                    rec.total_idle = 0  
        else:
            for rec in self:
                rec.total_idle = 0 

  
    def _compute_lost_hours(self):
        for rec in self:
            rec.lost_hours = rec.total_break + rec.total_idle

    def _compute_actual_work(self):
        for rec in self:
            rec.actual_work = rec.total_work - rec.lost_hours

    def _create_record_time_mngmnt(self):
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            self.create({'employee_id':emp.id,'date':datetime.today()})