from odoo import fields, models, api
import time










class NotificationManager(models.Model):

    _name = "user.notify"
    _description = "Notification Management For Odoo System"

    name = fields.Char(required=True, string="Name", help="Name of the rule")
    is_read = fields.Boolean(string="Read",
                             help="Enabling we can track all read activities "
                                  "It will track all your read activity that "
                                  "may increase the size of the log that may "
                                  "cause some problem with your data base")
    is_write = fields.Boolean(string="Write",
                              help="Enabling we can track all write activities")
    is_create = fields.Boolean(string="Create",
                               help="Enabling we can track all create activities")
    is_delete = fields.Boolean(string="Delete",
                               help="Enabling we can track all delete activities")
    is_all_users = fields.Boolean(string="All Users",
                                  help="Enabling we can track activities of all users")
    user_ids = fields.Many2many('res.users', string="Users",
                                help="Manage users")
    model_ids = fields.Many2many('ir.model', string="Model",
                                 help='Used to select which model is to track')
    notification_content = fields.Char(required=True, string="Notification Content", help="Content of the notification")


    @api.model
    def create_audit_log_for_create(self, res_model):
        """ Used to create user audit log based on the create operation """
        model_id = self.env['ir.model'].search([('model', '=', res_model)]).id
        notify = self.search([('model_ids', 'in', model_id)])
        if notify and notify.is_create:
            notification_ids = [((0, 0, {
            'res_partner_id': self.env.user.partner_id.id,
            'notification_type': 'inbox'}))]
            user_id = self.env.user.id
            message = str(self.name) + " record created"
            self.env.ref('mail.channel_all_employees').message_post(author_id=user_id,
                                body=(message),
                                message_type='comment',
                                subtype_xmlid="mail.mt_comment",
                                notification_ids=notification_ids,
                                partner_ids=[self.env.user.id],
                                notify_by_email=False,
                                )
        return res_model

    
    @api.model
    def create_audit_log_for_read(self, res_model, record_id):
        """ Used to create user audit log based on the read operation """
        model_id = self.env['ir.model'].search([('model', '=', res_model)]).id
        notify = self.search([('model_ids', 'in', model_id)])
        if notify and notify.is_read:
            notification_ids = [((0, 0, {
            'res_partner_id': self.env.user.partner_id.id,
            'notification_type': 'inbox'}))]
            user_id = self.env.user.id
            message = "record readed"
            self.env.ref('mail.channel_all_employees').message_post(author_id=user_id,
                                body=(message),
                                message_type='comment',
                                subtype_xmlid="mail.mt_comment",
                                notification_ids=notification_ids,
                                partner_ids=[self.env.user.id],
                                notify_by_email=False,
                                )
        return res_model
    

    @api.model
    def create_audit_log_for_delete(self, res_model, record_id):
        """ Used to create user audit log based on the delete operation """
        model = self.env['ir.model'].search([('model', '=', res_model)])
        model_id = self.env[res_model].browse(record_id)
        notify = self.search([('model_ids', 'in', model.id)])
        if notify and notify.is_delete and record_id and model_id:
            notification_ids = [((0, 0, {
            'res_partner_id': self.env.user.partner_id.id,
            'notification_type': 'inbox'}))]
            user_id = self.env.user.id
            message = "record deleted"
            self.env.ref('mail.channel_all_employees').message_post(author_id=user_id,
                                body=(message),
                                message_type='comment',
                                subtype_xmlid="mail.mt_comment",
                                notification_ids=notification_ids,
                                partner_ids=[self.env.user.id],
                                notify_by_email=False,
                                )
        return res_model
    


    @api.model
    def create_audit_log_for_write(self, res_model, record_id):
        """ Used to create user audit log based on the write operation """
        model_id = self.env['ir.model'].search([('model', '=', res_model)]).id
        notify = self.search([('model_ids', 'in', model_id)])
        if notify and notify.is_write:
            notification_ids = [((0, 0, {
            'res_partner_id': self.env.user.partner_id.id,
            'notification_type': 'inbox'}))]
            user_id = self.env.user.id
            message = "record updated"
            self.env.ref('mail.channel_all_employees').message_post(author_id=user_id,
                                body=(message),
                                message_type='comment',
                                subtype_xmlid="mail.mt_comment",
                                notification_ids=notification_ids,
                                partner_ids=[self.env.user.id],
                                notify_by_email=False,
                                )
        return res_model


class TaskNotification(models.Model):
    _inherit = "project.task"


    def _message_post_after_hook(self, message, msg_vals):
        if message.attachment_ids and not self.displayed_image_id:
            image_attachments = message.attachment_ids.filtered(lambda a: a.mimetype == 'image')
            if image_attachments:
                self.displayed_image_id = image_attachments[0]

        if self.email_from and not self.partner_id:
            # we consider that posting a message with a specified recipient (not a follower, a specific one)
            # on a document without customer means that it was created through the chatter using
            # suggested recipients. This heuristic allows to avoid ugly hacks in JS.
            email_normalized = tools.email_normalize(self.email_from)
            new_partner = message.partner_ids.filtered(
                lambda partner: partner.email == self.email_from or (email_normalized and partner.email_normalized == email_normalized)
            )
            if new_partner:
                if new_partner[0].email_normalized:
                    email_domain = ('email_from', 'in', [new_partner[0].email, new_partner[0].email_normalized])
                else:
                    email_domain = ('email_from', '=', new_partner[0].email)
                self.search([
                    ('partner_id', '=', False), email_domain, ('stage_id.fold', '=', False)
                ]).write({'partner_id': new_partner[0].id})
        # use the sanitized body of the email from the message thread to populate the task's description
        if not self.description and message.subtype_id == self._creation_subtype() and self.partner_id == message.author_id:
            self.description = message.body
        assigs = []    
        for assig in self.user_ids:
            assigs.append(assig.id)    
        self.update_notify("Log notes have been updated in task " + "(" +self.name + ")",assigs)    
        return super(TaskNotification, self)._message_post_after_hook(message, msg_vals)
    def update_notify(self,message,userList):
        if len(userList) > 0:
            display_msg = message
            
           
            post = self.env['res.partner'].search([('id','=',1)]).message_post(body=display_msg, message_type='notification', subtype_xmlid='mail.mt_comment',author_id=self.env.user.partner_id.id)

            if post:
                 for userid in userList:
                     user = self.env['res.users'].search([('id','=',userid)])
                     notification_ids = [((0, 0, {
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox'}))]
                     post.write({'notification_ids': notification_ids})

                
    def write(self,vals):

        assig_old = []
        assig_new = []
        for assig in self.user_ids:
            assig_old.append(assig.id)        
        final_assigs = assig_old  
        if 'user_ids' in vals:
            assig_new = vals['user_ids'][0][2]
            final_assigs = assig_new
            users_removed = []
            for element in assig_old:
                if element not in assig_new:
                    users_removed.append(element)            
            self.update_notify("You have been removed from task " + "(" + self.name + ")" ,users_removed)        
            users_added = []
            for element in assig_new:
                if element not in assig_old:
                    users_added.append(element)
            self.update_notify("You have been assigned to task " + "(" + self.name + ")" ,users_added)        
        final_assigs.append(self.manager_id.id)    
        if 'name' in vals:
            message = 'Name of the task ('  +self.name+ ') has been updated to (' + vals['name'] + ')'
            self.update_notify(message,final_assigs)
        if 'date_from' in vals:
            message = 'The start date of the task '  + "(" + self.name + ")" + ' has been changed from ' + str(self.date_from) + ' to ' + vals['date_from']
            self.update_notify(message,final_assigs)
        if 'date_to' in vals:
            message = 'The end date of the task '  + "(" + self.name + ")" + ' has been changed from ' + str(self.date_to) + ' to ' + vals['date_to']
            self.update_notify(message,final_assigs)
        if 'stage_id' in vals:
            stage_old = 'None'
            stage_new = 'None'
            if self.stage_id:
                stage_old = self.stage_id.name
            if self.env['project.task.type'].browse(vals['stage_id']).name:
                stage_new = self.env['project.task.type'].browse(vals['stage_id']).name
            message = 'Stage of the task ('  + self.name + ') has been changed from ' + stage_old + ' to ' + stage_new
            self.update_notify(message,final_assigs)
        if 'checklists' in vals:
            message = 'Checklist item status has been updated in task ('  + self.name + ')'
            self.update_notify(message,final_assigs)
        super(TaskNotification,self).write(vals)