# inherit res.partner model with fields to store shopify customer id and shopify instance id
import json

import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shopify_customer_id = fields.Char('Shopify Customer Id')
    shopify_instance_id = fields.Many2one('shopify.instance', string='Shopify Instance')
    shopify_instance_ids = fields.Many2many('shopify.instance', string='Shopify Instances')
    is_shopify_customer = fields.Boolean('Is Shopify Customer', default=False)
    shopify_order_count = fields.Integer('Shopify Order Count')
    shopify_note = fields.Text('Shopify Note')
    is_exported = fields.Boolean(string="Exported")

    # create method to import customers from shopify to odoo using rest api
    def import_shopify_customers(self, shopify_instance_ids, skip_existing_customer):
        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active','=',True)])
        for shopify_instance_id in shopify_instance_ids:
            # get url from shopify instance
            url = self.get_customer_url(shopify_instance_id, endpoint='customers.json')
            access_token = shopify_instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token,
            }
            params = {
                "limit": 250,  # Adjust the page size as needed
                "page_info": None
            }

            all_customers = []
            while True:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200 and response.content:
                    shopify_customers = response.json()
                    customers = shopify_customers.get('customers', [])
                    all_customers.extend(customers)
                    page_info = shopify_customers.get('page_info', {})
                    if 'has_next_page' in page_info and page_info['has_next_page']:
                        params['page_info'] = page_info['next_page']
                    else:
                        break
                else:
                    break

            if all_customers:
                customers = self.create_customers(all_customers, shopify_instance_id, skip_existing_customer)
                return customers
            else:
                _logger.info("Customers not found in shopify store")
                return []

    def get_customer_url(self, shopify_instance_id, endpoint):
        shop_url = "https://{}.myshopify.com/admin/api/{}/{}".format(shopify_instance_id.shopify_host,
                                                                     shopify_instance_id.shopify_version, endpoint)
        return shop_url

    def create_customers(self, customers, shopify_instance_id, skip_existing_customer):
        # check if shopify instance id is present
        customer_list = []

        for shopify_customer in customers:
            tags = shopify_customer.get('tags')
            tag_list = []
            if tags:
                tags = tags.split(',')
                for tag in tags:
                    tag_id = self.env['res.partner.category'].sudo().search([('name', '=', tag)], limit=1)
                    if not tag_id:
                        tag_id = self.env['res.partner.category'].sudo().create({'name': tag})
                        tag_list.append(tag_id.id)
                    else:
                        tag_list.append(tag_id.id)
            address = shopify_customer.get('addresses')
            street = street2 = city = zip = ""
            country_id = False
            if address:
                street = address[0].get('address1') if address[0].get('address1') else ""
                street2 = address[0].get('address2') if address[0].get('address2') else ""
                city = address[0].get('city') if address[0].get('city') else ""
                zip = address[0].get('zip') if address[0].get('zip') else ""
                country_code = address[0].get('country_code')
                country_id = self.env['res.country'].sudo().search(
                    [('code', '=', country_code)], limit=1)

            if shopify_customer.get('first_name') and shopify_customer.get('last_name'):
                name = shopify_customer.get(
                    'first_name') + ' ' + shopify_customer.get('last_name')
            elif shopify_customer.get('first_name'):
                name = shopify_customer.get('first_name')
            else:
                name = shopify_customer.get('last_name')
            if name:
                customer_vals = {
                    'shopify_customer_id': shopify_customer.get('id'),
                    'name': name,
                    'email': shopify_customer.get('email'),
                    'phone': shopify_customer.get('phone'),
                    'shopify_instance_id': shopify_instance_id.id,
                    'is_shopify_customer': True,
                    'shopify_order_count': shopify_customer.get('orders_count'),
                    'shopify_note': shopify_customer.get('note'),
                    'street':street,
                    'street2':street2,
                    'city':city,
                    'zip':zip,
                    'country_id':country_id.id if country_id else False
                }

                # check if shopify customer id is present in res.partner using id
                customer = self.env['res.partner'].search(
                    [('shopify_customer_id', '=', shopify_customer.get('id'))],limit=1)
                # check if customer is present
                if customer:
                    if skip_existing_customer == False:
                        # update customer details
                        customer.sudo().write(customer_vals)
                        customer.category_id = [(5, 0, 0)]
                        customer.category_id = [(4, val) for val in tag_list]
                else:
                    # create customer in odoo
                    customer = self.env['res.partner'].sudo().create(customer_vals)
                    customer.category_id = [(4, val) for val in tag_list]
                customer_list.append(customer.id)

        return customer_list

    def export_customers_to_shopify(self, shopify_instance_ids,update):
        partner_ids = self.sudo().browse(self._context.get("active_ids"))
        if not partner_ids:
            if update == False:
                partner_ids = self.sudo().search([('is_shopify_customer','=',False),('is_exported','=',False)])
            else:
                partner_ids = self.sudo().search([])

        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for instance_id in shopify_instance_ids:
            url = self.get_customer_url(instance_id, endpoint='customers.json')

            access_token = instance_id.shopify_shared_secret

            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }

            for partner in partner_ids:
                tag_vals = ','.join(str(tag.name) for tag in partner.category_id) if partner.category_id else ''

                if partner.is_shopify_customer and partner.shopify_instance_id.id == instance_id.id and update == True:
                    end = "customers/{}.json".format(partner.shopify_customer_id)
                    url = self.get_customer_url(instance_id, endpoint=end)
                    data = {
                        "customer": {
                            "id": partner.shopify_customer_id,
                            "email": partner.email,
                            "note": partner.shopify_note,
                            "phone":partner.phone,
                            "tags":tag_vals,
                            "addresses": [
                                {
                                    "address1": partner.street if partner.street else "",
                                    "city": partner.city if partner.city else "",
                                    # "province": "ON",
                                    "phone": partner.phone if partner.phone else "",
                                    "zip": partner.zip if partner.zip else "",
                                    "last_name": "",
                                    "first_name": partner.name,
                                    "country": partner.country_id.code if partner.country_id else ""
                                }
                            ],
                        }
                    }
                    response = requests.put(url, headers=headers, data=json.dumps(data))
                else:
                    if not partner.is_shopify_customer:
                        data = {
                            "customer": {
                                "first_name": partner.name,
                                "last_name": "",
                                "email": partner.email if partner.email else "",
                                "phone": partner.phone if partner.phone else "",
                                "verified_email": True,
                                "tags": tag_vals,
                                "addresses": [
                                    {
                                        "address1": partner.street if partner.street else "",
                                        "city": partner.city if partner.city else "",
                                        # "province": "ON",
                                        "phone": partner.phone if partner.phone else "",
                                        "zip": partner.zip if partner.zip else "",
                                        "last_name": "",
                                        "first_name": partner.name,
                                        "country": partner.country_id.code if partner.country_id else ""
                                    }
                                ],
                                "password": "",
                                "password_confirmation": "",
                                "send_email_welcome": False
                            }
                        }

                        response = requests.post(url, headers=headers, data=json.dumps(data))
                if response:
                    if response.content:
                        shopify_customers = response.json()
                        customer = shopify_customers.get('customer', [])
                        if customer:
                            partner.is_shopify_customer = True
                            partner.shopify_customer_id = customer.get('id')
                            partner.shopify_instance_id = instance_id.id
                            partner.is_exported = True
                            _logger.info("customer created/updated successfully")
                    else:
                        _logger.info("customer creation/updation failed")
                        _logger.info(response.content)
                else:
                    _logger.info("Nothing created / updated")


    def action_open_export_customer_to_shopify(self):
        action = {
            'name': _('Export Customers to Shopify'),
            'res_model': 'customer.export.instance',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {},
        }
        return action




















