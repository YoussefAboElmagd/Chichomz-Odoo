# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from odoo import models, fields, api



    
class ProjectTaskTimer(models.Model):
    _inherit = 'attendance.breaktime'

    break_timer = fields.Boolean(string='Toggle Timer', default=False)
    is_user_working = fields.Boolean(
        'Is Current User Working',
        help="Technical field indicating whether the current user is working. ")
    duration = fields.Float(
        'Duration', compute='_compute_duration', store=True)
    first_time = fields.Boolean('Is It First Time To Use The Timer', default=True)

    def _compute_duration(self):
        self



    @api.model
    @api.constrains('break_timer')
    def toggle_start(self):
        if self.break_timer is True:
            self.write({'is_user_working': True})
            self.break_start = datetime.now()
            self.env.user.is_on_break = True


        else:
            self.write({'is_user_working': False})
            self.write({'break_finish': fields.Datetime.now()})
            self.break_duration = (datetime.now() - self.break_start).total_seconds() / 60
            self.first_time = False
            self.env.user.is_on_break = False

            

    def get_working_duration(self):
        """Get the additional duration for 'open times'
        i.e. productivity lines with no date_end."""
        duration = 0
        if type(self.break_start) != datetime:
            duration = 0
        else:
            duration = (datetime.now() - self.break_start).total_seconds() / 60
                
        return duration
