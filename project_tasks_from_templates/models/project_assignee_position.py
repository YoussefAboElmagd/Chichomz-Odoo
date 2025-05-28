from odoo import fields, models

class ProjectAssigneePosition(models.Model):
   
    _name = 'project.assignee.position'
    _description = 'Get Position of Assignee'

    position_assignee_id = fields.Many2one('project.project', string='Assignee Position')
    template_user_ids = fields.Many2many('res.users', string ='Assignee')
    template_job_pos= fields.Many2many('tgrba.jobpos', string ='Job Position')