from odoo import api, models, fields

class JobPosition(models.Model):
    _name = "tgrba.jobpos"
    name = fields.Char(string="job_pos")

class job_Position(models.Model):
    _inherit ='project.task'
    job_pos= fields.Many2many('tgrba.jobpos', string ='Job Position')
    
   

    

