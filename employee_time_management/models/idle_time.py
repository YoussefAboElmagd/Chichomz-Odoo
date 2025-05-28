from odoo import fields, models, api
from datetime import datetime


class IdleTime(models.Model):
    _name = 'attendance.idle.time'

    def _default_employee(self):
        return self.env.user.employee_id
    

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True, readonly=True)
    idle_start = fields.Datetime(string="Idle Start", readonly=True)
    idle_finish = fields.Datetime(string="Idle End", readonly=True)
    idle_duration = fields.Float(string='Idle Time', store=True, readonly=True)



    def createRecordIdle(self,start_date,end_date):
        # s_date = datetime.strptime(start_date, "%a, %d %b %Y %H:%M:%S %Z")
        # e_date = datetime.strptime(end_date, "%a, %d %b %Y %H:%M:%S %Z")
        if not self.env.user.is_on_break:
            s_date = datetime.fromtimestamp(start_date/1000.0)
            e_date = datetime.fromtimestamp(end_date/1000.0)
            duration = (e_date - s_date).total_seconds() / 60
            if (duration > 0):
                vals = {'idle_start':s_date,'idle_finish':e_date, 'idle_duration':duration}
                self.create(vals)



