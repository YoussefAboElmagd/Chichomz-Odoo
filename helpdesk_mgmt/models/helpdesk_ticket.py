from datetime import datetime, timedelta
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError


class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _order = "priority desc, sequence, number desc, id desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    def _get_default_stage_id(self):
        return self.env["helpdesk.ticket.stage"].search([], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["helpdesk.ticket.stage"].search([])
        return stage_ids

    number = fields.Char(string="Ticket number", default="/", readonly=True)
    name = fields.Char(string="Title", required=True)
    description = fields.Html(required=True, sanitize_style=True)
    x_due_date = fields.Date(string="Due Date", required=True)

    def default_desc_rw(self):
        return False
    loc_desc = fields.Boolean(default=default_desc_rw)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned user",
        tracking=True,
        required= True,
        index=True,
        domain="team_id and [('share', '=', False),('id', 'in', user_ids)] or [('share', '=', False)]",  # noqa: B950
    )
    user_id_public = fields.Many2one(
        comodel_name="res.users",
        string="Assigned user",
        tracking=True,
        index=True,
        domain="team_id and [('share', '=', False),('id', 'in', user_ids)] or [('share', '=', False)]",
        related="user_id"  # noqa: B950
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    is_stage_locked = fields.Boolean(default=True,compute='_compute_user_in_team')
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        default=_get_default_stage_id,
        tracking=True,
        ondelete="restrict",
        index=True,
        copy=False,
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer Name",
                                 domain="[('x_type_client', '!=', 'supplier'),('x_type_client', '!=', 'employee')]", required=True)
    partner_name = fields.Char(string="Customer Number" , required= True)
    partner_email = fields.Char(string="Customer Email")
    supplier_id = fields.Many2one(
        comodel_name="res.partner", string="NEW Supplier Name", domain="[('x_type_client', '=', 'supplier')]" )
    Supplier_number = fields.Char(string="Supplier Number")
    Supplier_email = fields.Char(string="Supplier Email")
    order_number = fields.Char(string="NEW Order Id" , required= True)

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    assigned_date = fields.Datetime()
    closed_date = fields.Datetime()
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.tag", string="Tags")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
       
        help="Channel indicates where the source of a ticket"
        "comes from (it could be a phone call, an email...)",
    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Type",


    )
    # x_category_id = fields.Char(
    #     compute='_compute_x_category_id', string='category name')

    # @api.onchange("category_id")
    # def _compute_x_category_id(self):
    #     self.x_category_id = self.category_id.name
    #     print('------------------', self.category_id.name)

    x_category_id = fields.Selection(
        selection=[
            ("na", "test"),
            ("", "emp"),
            ("1", "test1"),
            ("refund_request", "Refund Request"),
            ("complaint", "Complaint"),
            ("order_reassign", "Order Reassign"),
            ("update_in_payment", "Update in Payment"),
            ("payment_fees", "PAYMENT FEES"),
            ('paymob_link', 'Paymob Link payments'),
            ('bank_transfer', 'Bank Transfer'),
            ('vf_cash', 'VF Cash Payment'),
            ('stripe', 'Stripe Payment'),
            ('supplier_shipping', 'Supplier Shipping Cost Change'),
            ('deduction_from_customer', 'Deduction From Customer'),
            ('deposit_transfer', 'Deposit Transfer'),
            ('cash_payments', 'Cash Payments'),
            ('wrong_cost', 'Wrong Cost'),
            ('extra_shipping_fees', 'Extra Shipping Fees'),
          
        ],
        string="Type",
    
        

    )
    paid_at = fields.Selection(
        selection=[
            ("showroom", "Showroom"),
            ("sales", "Sales"),
        ],
        string="Paid at"

    )
    
    amount_for_supplier = fields.Selection(
     selection=[
            ("chicomz", "Chicomz"),
            ("customer","Customer"),
            ("supplier name", "Supplier name"),
            
        ], 
        string="Amount for Supplier")
        
        
        
    
    

    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Assigned To Team",
        tracking=True,
        
        index=True,
    )
    team_id_public = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Assigned To Team",
        related="team_id",
        tracking=True,
        index=True,
    )
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        default="1",
        
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket")],
        string="Media Attachments",
    )
    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
    )
    sequence = fields.Integer(
        index=True,
        default=10,
        help="Gives the sequence order when displaying a list of tickets.",
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    @api.onchange("partner_id", "supplier_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.phone
            self.partner_email = self.partner_id.email

    @api.onchange("supplier_id")
    def _onchange_supplier_id(self):
        if self.supplier_id:
            self.Supplier_number = self.supplier_id.phone
            self.Supplier_email = self.supplier_id.email
    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    def _creation_subtype(self):
        return self.env.ref("helpdesk_mgmt.hlp_tck_created")

    @api.model_create_multi
    def create(self, vals_list):
        user_ids = False
        for vals in vals_list:
            if vals.get("number", "/") == "/":
                vals["number"] = self._prepare_ticket_number(vals)
            if vals.get("user_id") and not vals.get("assigned_date"):
                vals["assigned_date"] = fields.Datetime.now()
            vals['loc_desc'] = True
            if vals.get("create_uid"):
                teams = self.env['helpdesk.ticket.team'].sudo().search([
                    ('user_ids', '=', vals['create_uid'])
                ], limit=1)
                if teams:
                    vals['x_team_id'] = teams.id  # assign the first found team
            if vals.get("team_id"):
                team = self.env['helpdesk.ticket.team'].search([('id', '=', int(vals['team_id']))], limit=1)
                user_ids = team.user_ids
        res = super().create(vals_list)        
        if user_ids:
            for user in user_ids:
                res.message_subscribe([user.partner_id.id])
                post = res.message_post(subject=res.name,body=user.partner_id.name+" have been assigned to the ticket")
        #         if post:
        #             notification_ids = []
        #             notification_ids.append((0, 0, {'res_partner_id': user.partner_id.id, 'mail_message_id': post.id}))
        # # notification_ids = [(0, 0, {'res_partner_id': user.partner_id.id, 'mail_message_id': message.id}) for user in self.user_ids]
        #             post.write({'notification_ids': notification_ids})

        return res

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):

        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse(
                    [vals["stage_id"]])
                vals["last_stage_update"] = now
                _ticket.message_post(body="Stage has been changed from "+_ticket.stage_id.name+" to "+stage.name)
                if stage.closed:
                    vals["closed_date"] = now
                if vals["stage_id"] == 4 or vals["stage_id"] == 5 or vals["stage_id"] == 6:
                    vals["is_stage_locked"] = True
            if vals.get("user_id"):
                vals["assigned_date"] = now
        return super().write(vals)

    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/ticket/%s" % (item.id)
        return res
    

    @api.model
    def message_post(self, **kwargs):
        # Call the super method to post the message
        message = super().message_post(**kwargs)
        
        # notification_ids = []
        # for user in self.user_ids:
        #     if message.author_id.id != user.partner_id.id:
        #         notification_ids.append(((6, 0, {
        #                 'res_partner_id': user.partner_id.id,
        #                 'notification_type': 'inbox'})))
        if self.team_id.send_notifications:
            notification_ids = []
            for user in self.user_ids:
                if user.id != self.env.user.id and user.id != message.author_id.id and user.id != self.user_id.id and user.id != self.team_id.alias_user_id.id and user.id != self.team_id.user_id.id and user.partner_id.id not in message.notification_ids.mapped('res_partner_id').ids:
                    notification_ids.append((0, 0, {'res_partner_id': user.partner_id.id, 'mail_message_id': message.id}))
            # notification_ids = [(0, 0, {'res_partner_id': user.partner_id.id, 'mail_message_id': message.id}) for user in self.user_ids]
            message.write({'notification_ids': notification_ids})

        
        return message

    # def _send_internal_note_notification(self, message):
    #     # Define your notification logic here
    #     # You can send an email or post a message to followers, groups, etc.
        
    #     # Example: Notify followers of the record
    #         # self.env['mail.message'].create({'message_type':"notification",
    #         #     "subtype_id": self.env.ref("mail.mt_comment").id,
    #         #     'body': "Message body",
    #         #     'subject': "Message subject",
    #         #     'partner_ids': [(4, 512)],
    #         #     'model': self._name,
    #         #     'res_id': self.id,
    #         #     })
    #         # self.env.user.partner_id.message_post(
    #         #     body=f"Internal Note added to {self.name}: {message.body}",
    #         #     subject="New Internal Note",
    #         #     message_type='notification'
    #         # )
    #         post = self.env['helpdesk.ticket'].search([('id','=',self.id)]).message_post(subject=message.author_id.name,body=message.body, message_type='notification', subtype_xmlid='mail.mt_comment',author_id=message.author_id.id)

    #         if message:
    #             for user in self.user_ids:
    #                 notification_ids = [((0, 0, {
    #                 'res_partner_id': user.partner_id.id,
    #                 'notification_type': 'inbox'}))]
    #                 message.write({'notification_ids': notification_ids})
    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    # def _track_template(self, tracking):
    #     res = super()._track_template(tracking)
    #     ticket = self[0]
    #     if "stage_id" in tracking and ticket.stage_id.mail_template_id:
    #         res["stage_id"] = (
    #             ticket.stage_id.mail_template_id,
    #             {
    #                 # Need to set mass_mail so that the email will always be sent
    #                 "composition_mode": "mass_mail",
    #                 "auto_delete_message": True,
    #                 "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
    #                     "mail.mt_note"
    #                 ),
    #                 "email_layout_xmlid": "mail.mail_notification_light",
    #             },
    #         )
    #     return res

    # @api.model
    # def message_new(self, msg, custom_values=None):
    #     """Override message_new from mail gateway so we can set correct
    #     default values.
    #     """
    #     if custom_values is None:
    #         custom_values = {}
    #     defaults = {
    #         "name": msg.get("subject") or _("No Subject"),
    #         "description": msg.get("body"),
    #         "partner_email": msg.get("from"),
    #         "partner_id": msg.get("author_id"),
    #     }
    #     defaults.update(custom_values)

    #     # Write default values coming from msg
    #     ticket = super().message_new(msg, custom_values=defaults)

    #     # Use mail gateway tools to search for partners to subscribe
    #     email_list = tools.email_split(
    #         (msg.get("to") or "") + "," + (msg.get("cc") or "")
    #     )
    #     partner_ids = [
    #         p.id
    #         for p in self.env["mail.thread"]._mail_find_partner_from_emails(
    #             email_list, records=ticket, force_create=False
    #         )
    #         if p
    #     ]
    #     ticket.message_subscribe(partner_ids)

    #     return ticket

    # def message_update(self, msg, update_vals=None):
    #     """Override message_update to subscribe partners"""
    #     email_list = tools.email_split(
    #         (msg.get("to") or "") + "," + (msg.get("cc") or "")
    #     )
    #     partner_ids = [
    #         p.id
    #         for p in self.env["mail.thread"]._mail_find_partner_from_emails(
    #             email_list, records=self, force_create=False
    #         )
    #         if p
    #     ]
    #     self.message_subscribe(partner_ids)
    #     return super().message_update(msg, update_vals=update_vals)

    # def _message_get_suggested_recipients(self):
    #     recipients = super()._message_get_suggested_recipients()
    #     try:
    #         for ticket in self:
    #             if ticket.partner_id:
    #                 ticket._message_add_suggested_recipient(
    #                     recipients, partner=ticket.partner_id, reason=_(
    #                         "Customer")
    #                 )
    #             elif ticket.partner_email:
    #                 ticket._message_add_suggested_recipient(
    #                     recipients,
    #                     email=ticket.partner_email,
    #                     reason=_("Customer Email"),
    #                 )
    #     except AccessError:
    #         # no read access rights -> just ignore suggested recipients because this
    #         # imply modifying followers
    #         return recipients
    #     return recipients

    # def _notify_get_reply_to(self, default=None):
    #     """Override to set alias of tasks to their team if any."""
    #     aliases = self.sudo().mapped("team_id")._notify_get_reply_to(default=default)
    #     res = {ticket.id: aliases.get(ticket.team_id.id) for ticket in self}
    #     leftover = self.filtered(lambda rec: not rec.team_id)
    #     if leftover:
    #         res.update(
    #             super(HelpdeskTicket, leftover)._notify_get_reply_to(
    #                 default=default)
    #         )
    #     return res
    create_by_team = fields.Char(
        string="Created By Team", compute='_compute_create_by_team')

    @api.depends('create_uid')
    def _compute_create_by_team(self):
        for record in self:
            if record.create_uid:

                record.create_by_team = record.env['helpdesk.ticket.team'].search(
                    [('user_ids', '=', record.create_uid.name)]).name
            else:
                record.create_by_team = "No Team"

# new fields for form in ticket
    cancellation_reason = fields.Selection(
        selection=[
            ("client", "Client"),
            ("internal", "Internal"),
            ("supplier", "Supplier"),
        ],
        string="Cancellation reason:"
    )
    refund_amount_ = fields.Float(string="Refund Amount:")

    refund_method = fields.Selection([
        ('paymob', 'Paymob'),
        ('vodafone_cash', 'Vodafone cash'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank transfer')
    ], string="Refund method:")

    item_sku = fields.Char(string="Item Sku:")
    ticket_sla = fields.Float(string="Ticket Sla:")
    customer_request = fields.Selection(
        selection=[
            ("maintenance", "Maintenance"),
            ("replacement", "Replacement"),
            ("refund", "Refund"),
            ("late delivery", "Late Delivery"),
        ],
        string="Customer Request:"
    )
    penalty = fields.Selection(
        selection=[
            ("yes", "YES"),
            ("no", "NO"),

        ],
        string="Penalty:"
    )
    penalty_amount = fields.Float(string="Penalty Amount:")
    supplier_feedback = fields.Char(string=" Supplier feedback:")
    attachment_d = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",

        string=" Attachments",
    )
    old_supplier = fields.Many2one(
        comodel_name="res.partner", string="OLD supplier :", domain="[('x_type_client', '=', 'supplier')]")
    new_product_cost = fields.Float(string="NEW Product Cost :")
    old_product_cost = fields.Float(string="OLD Product Cost :")
    old_shipping_cost = fields.Float(string="OLD Shipping Cost :")
    new_shipping_cost = fields.Float(string="NEW Shipping Cost :")

    difference_in_shipping_cost = fields.Selection(
        selection=[
            ("paid_by_chichomz", "Paid By CHICHOMZ"),
            ("paid_bto_chichomz", "Paid TO CHICHOMZ"),

        ],
        string="Difference in Shipping Cost:"
    )

    old_payment_method = fields.Selection(
        selection=[
            ("paymob", "PAYMOB"),
            ("cash", "CASH"),
            ("vf_cash", "VF CASH"),
            ("bank_transfer", "BANK TRANSFER"),

        ],
        string="OLD Payment Method:"
    )
    new_payment_method = fields.Selection(
        selection=[
            ("paymob", "PAYMOB"),
            ("cash", "CASH"),
            ("vf_cash", "VF CASH"),
            ("bank_transfer", "BANK TRANSFER"),

        ],
        string="NEW Payment Method:"
    )
    total_order_amount = fields.Float(string="Total Order Amount:")
    paid_amount = fields.Float(string="Paid Amount:")
    remaining_amount_to_be_collected = fields.Float(
        string="Remaining Amount To Be Collected:")

    payment_method = fields.Selection(
        selection=[
            ("forsa", "Forsa"),
            ("aman", "Aman"),
            ("souholaa", "Souholaa"),
            ("valu", "Valu"),
            ("sympl", "Sympl"),
            ("premium", "Premium"),
            ("contact", "Contact"),

        ],
        string="Payment Method:"
    )
    required_fees = fields.Float(string="Required Fees :")
    receipt_image = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",

        string="Receipt Image",
    )

    payment_link = fields.Char(string="Payment Link:")
    payment_screenshot = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",

        string="Payment Screenshot:",
    )
    transfer_from_number = fields.Integer(string="Transfer From Number :")
    transfer_to_number = fields.Integer(string="Transfer To Number :")
    the_real_amount_to_consider_it = fields.Float(
        string="The Real Amount To Consider It:")
    the_agreed_shipping_cost_with_supplier = fields.Float(
        string="The Agreed Shipping Cost With The Supplier:")
    Screenshot_from_the_agreement = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",

        string="Screenshot From The Agreement:",
    )
    amount_deducted_from_the_customer = fields.Float(
        string="Amount Deducted From The Customer:")
    canceled_product_sku = fields.Char(
        string="Cancelled Product Sku:")
    old_order_id = fields.Char(
        string="OLD Order Id:")
    new_product_sku = fields.Char(
        string="NEW Product Sku:")
    reason = fields.Char(
        string="Reason", default="Write it in the description", readonly=True)
  
    x_team_id= fields.Many2one('crm.team' ,string='Created BY Team')



    @api.onchange('create_uid')
    def _compute_team_name(self):
        for ticket in self:
            teams = self.env['helpdesk.ticket.team'].search([('user_ids','=',ticket.create_uid.id)])
            for team in teams:
                if ticket.x_team_id:
                    continue
                ticket.x_team_id=team.id

    def _compute_user_in_team(self):
        if self.team_id:
            if  self.env.user in self.user_ids:
                self.is_stage_locked = True
            else:
                self.is_stage_locked = False
        else:
            self.is_stage_locked = False
            
            
            
       # requests_chichomz 
    
    
     # Penalty
    penalty = fields.Selection(
        selection=[
            ("n/a", "N/A"),
            ("yes", "YES"),
            ("no", "NO"),
        ],
        string="Penalty" ,

    )

    # Route Cause
    route_cause = fields.Selection(
        selection=[
            ("n/a", "N/A"),
            ("customer_side", "Customer Side"),
            ("company_side", "Company Side"),
            ("supplier_side", "Supplier Side"),
        ],
        string="Route Cause",
        )

    # Team (Static Selection)
    team = fields.Selection(
        selection=[
            ("n/a", "N/A"),
            ("back_office", "Back Office"),
            ("showroom", "Showroom"),
            ("indoor_sales", "Indoor Sales"),
            ("customer_care", "Customer Care"),
            ("vendor_management", "Vendor Management"),
            ("operation", "Operation"),
            ("content", "Content"),
            ("warehouse", "Warehouse"),
        ],
        string="Team" , 

    )

    # Retention
    retention = fields.Selection(
        selection=[
            ("n/a", "N/A"),
            ("new_order", "New Order"),
            ("extra_discount", "Extra Discount"),
            ("discount_voucher", "Discount Voucher"),
            ("gift_voucher", "Gift Voucher"),
            ("issue_solved", "Issue Solved"),
            ("refused", "Refused"),
        ],
        string="Retention" ,

    )    
        
        
     # Complaint Feedback
    complaint_feedback = fields.Text(string="Complaint Feedback",)
    
    # 3. Complaint Type (Dropdown Menu)
    complaint_type = fields.Selection([
       
        ('quality', 'Quality'),
        ('damaged', 'Damaged'),
        ('late_delivery', 'Late Delivery'),
        ('not_matching', 'Not Matching'),
        ('shipping_issue', 'Shipping Issue'),
        ('changed_mind', 'Changed His Mind'),
        ('new_order', 'Created New Order'),
        ('refund', 'Refund'),
        ('warehouse_problem', 'Warehouse Problem'),
        ('missing_items', 'Missing Items'),
        ('maintenance', 'Need to Maintenance'),
        ('bad_attitude', 'Bad Attitude'),
        ('discount_issue', 'Discount Issue'),
        ('wrong_action', 'Wrong Action'),
        ('different_price', 'Different Price'),
        ('customer_attitude', 'Customer Attitude'),
        ('cant_manufacture', 'Can\'t Manufacturing'),
        ('out_of_stock', 'Out Of Stock'),
        ('fake_status', 'Fake Order Status'),
    ], string='Complaint Type' 
      
      )    
    new_title = fields.Char(string='Name',)
    
    # 4. Refund (Yes/No)
    refund = fields.Boolean(string='Refund',
     )

    # 5. Refund Amount (Open Field)
    refund_amount = fields.Float(string='Refund Amount' ,
     )
    
    # name = fields.char(string='Name', required=True)

   
    ticket_url = fields.Char(string='Ticket Link', compute='_compute_ticket_url', store=False ,
     )

    def _compute_ticket_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for ticket in self:
            if ticket.id:
                ticket.ticket_url = f'{base_url}/web#id={ticket.id}&model=helpdesk.ticket&view_type=form'
            else:
                ticket.ticket_url = ''
                
    skus = fields.Many2many(
        'helpdesk.ticket.sku',
        'helpdesk_ticket_main_sku_rel',
        'ticket_id', 'sku_id',
        string="SKUs"
    )            
                
   
    
    #  sla system
    
    sla_start_time = fields.Datetime(string="SLA Start Time", tracking=True)

    violation_timer = fields.Char(string="SLA Time Left", compute="_compute_violation_timer", store=True)
    is_violated = fields.Boolean(string="Violated", compute="_compute_violation_timer", store=True)

    risk_timer = fields.Char(string="Risk Timer", compute="_compute_risk_timer", store=True)
    is_risk = fields.Boolean(string="Risk", compute="_compute_risk_timer", store=True)

   
    
    @api.depends('sla_start_time', 'team_id')
    def _compute_violation_timer(self):
     for rec in self:
        if rec.sla_start_time and rec.team_id:
            now = fields.Datetime.now()

            # Determine SLA deadline based on team
            if rec.team_id.name == 'Compliant Team':
                deadline = rec.sla_start_time + timedelta(days=9)
            else:
                deadline = rec.sla_start_time + timedelta(hours=24)

            delta = deadline - now

            if delta.total_seconds() >= 0:
                # SLA still valid
                days = delta.days
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                rec.violation_timer = f"Remaining: {days}d {hours}h {minutes}m"
                rec.is_violated = False
            else:
                # SLA breached
                overdue = abs(delta)
                days = overdue.days
                hours, remainder = divmod(overdue.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                rec.violation_timer = f"Overdue: {days}d {hours}h {minutes}m"
                rec.is_violated = True
        else:
            rec.violation_timer = "0d 0h 0m"
            rec.is_violated = False


    @api.depends('create_date', 'stage_id')
    def _compute_risk_timer(self):
     for rec in self:
        now = fields.Datetime.now()
        if not rec.create_date:
            rec.risk_timer = "0d 0h 0m"
            rec.is_risk = False
            continue

        # Determine end time
        if rec.stage_id and rec.stage_id.name.lower() == 'done':
            end_time = rec.write_date or now
        else:
            end_time = now

        # Remaining time before 9-day risk
        risk_deadline = rec.create_date + timedelta(days=9)
        delta = risk_deadline - end_time

        # If ticket is already overdue
        if delta.total_seconds() < 0:
            overdue = abs(delta)
            days = overdue.days
            hours, remainder = divmod(overdue.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            rec.risk_timer = f"Overdue: {days}d {hours}h {minutes}m"
            rec.is_risk = not (rec.stage_id and rec.stage_id.name.lower() == 'done')
        else:
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            rec.risk_timer = f"Remaining: {days}d {hours}h {minutes}m"
            rec.is_risk = False

    @api.onchange('team_id')
    def _onchange_team_id_reset_timer(self):
        """Reset SLA timer when team is assigned or reassigned"""
        self.sla_start_time = fields.Datetime.now()
        
        
    user_has_group = fields.Boolean(string="User in Field Editor Group", compute='_compute_user_group', store=False)

    def _compute_user_group(self):
        for rec in self:
            rec.user_has_group = self.env.user.has_group('helpdesk_mgmt.group_helpdesk_field_editor')     
   

        