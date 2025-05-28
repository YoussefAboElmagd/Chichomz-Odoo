# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models,api


class ProjectProject(models.Model):
    """ This class extends the 'project.project' model to add a many2one
    field for selecting project task template.
    Methods:
        action_create_project_from_template():
            Creates a new project based on the selected project template.
        _create_task(item, parent):
            Creates a new project task for the given item and attaches
            it to the current project.
    """
    _inherit = 'project.project'

    project_template_id = fields.Many2one(
        'project.task.template',
        string='Project Template',
        help='Select a project task template to use for this project.')
    pos_assig_ids = fields.One2many('project.assignee.position', 'position_assignee_id', string='Assignee Position')    
    test_field = fields.Char('Test Output')
    test_field2 = fields.Char('Test Output 2')
    def action_create_project_from_template(self):
        """ Creates a new project based on the selected project template.
        Returns:
            dict: Action configuration to open the project form.
        """
        for item in self.project_template_id.task_ids:
            self._create_task(item, False)
        return {
            'view_mode': 'form',
            'res_model': 'project.project',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }
    @api.onchange('project_template_id')
    def _add_job_positions_used(self):
        for item in self.pos_assig_ids:
            item.unlink()
        job_pos_list = []
        for item in self.project_template_id.task_ids:
            job_pos_list.append(item.job_pos)
        job_pos_list = list(dict.fromkeys(job_pos_list))
        #lines = []
        if len(job_pos_list) > 0 :
            for pos_id in job_pos_list:
                #result ={'template_job_pos': pos_id}
                #lines.append((0,0, result))
                self.pos_assig_ids |= self.env['project.assignee.position'].new({
                       'template_job_pos': pos_id,

                  })
            #self.pos_assig_ids = lines
            

    @api.onchange('pos_assig_ids')
    def _print_test(self):
        if len(self.pos_assig_ids) > 0 :
            inp_str1 = str(self.pos_assig_ids[0].template_job_pos)
            inp_str2 = str(self.project_template_id.task_ids[0].job_pos)
            num1 = ""
            num2 = ""
            for c in inp_str1:
                if c.isdigit():
                    num1 = num1 + c
            for c in inp_str2:
                if c.isdigit():
                    num2 = num2 + c




    def _create_task(self, item, parent):
        """Creates a new project task for the given item and attaches it to
        the current project.
        Args:
            item (models.Model): project task
            parent (int): id of parent project task
        """
        inp_str2 = str(item.job_pos)
        num2 = ""
        for c in inp_str2:
            if c.isdigit():
                num2 = num2 + c 
        assig_pos_final = item.user_ids
        for temp_item in self.pos_assig_ids:
            inp_str1 = str(temp_item.template_job_pos)
            num1 = ""
            for c in inp_str1:
                if c.isdigit():
                    num1 = num1 + c
            if num1 == num2:
                assig_pos_final = temp_item.template_user_ids

        task = self.env['project.task'].sudo().create({
            'project_id': self.id,
            'name': item.name,
            'parent_id': parent,
            'stage_id': self.env['project.task.type'].search(
                [('sequence', '=', 1)], limit=1).id,
            'user_ids': assig_pos_final,
            'checklist_id': item.checklist_id.id,
            'planned_hours': item.planned_hours,
            'job_pos': item.job_pos,
            'description': item.description
            })
        for sub_task in item.child_ids:
            self._create_task(sub_task, task.id)
