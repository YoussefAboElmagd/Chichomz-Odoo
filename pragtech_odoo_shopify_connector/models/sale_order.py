# inherirt class sale.order and add fields for shopify instance and shopify order id
import datetime
import json

import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError


import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_instance_id = fields.Many2one('shopify.instance', string='Shopify Instance')
    shopify_order_id = fields.Char('Shopify Order Id')
    shopify_order_number = fields.Char('Shopify Order Number')
    shopify_order_status = fields.Char('Shopify Order Status')
    shopify_order_date = fields.Datetime('Shopify Order Date')
    shopify_order_total = fields.Float('Shopify Order Total')
    is_shopify_order = fields.Boolean('Is Shopify Order', default=False)
    is_exported = fields.Boolean(string="Is Exported")
    order_shopify_id = fields.Char(string="Shopify-Order ID")

    def import_shopify_draft_orders(self, shopify_instance_ids, skip_existing_order, from_date, to_date):
        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for shopify_instance_id in shopify_instance_ids:
            url = self.get_order_url(shopify_instance_id, endpoint='draft_orders.json')
            access_token = shopify_instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token
            }
            if from_date and to_date:
                params = {
                    "limit": 250,  # Adjust the page size as needed
                    "page_info": None,
                    "updated_at_min": from_date,
                    "updated_at_max": to_date,
                }
            else:
                params = {
                    "limit": 250,  # Adjust the page size as needed
                    "page_info": None,
                }
            all_orders = []

            while True:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200 and response.content:
                    draft_orders = response.json()
                    orders = draft_orders.get('draft_orders', [])
                    all_orders.extend(orders)
                    page_info = draft_orders.get('page_info', {})
                    if 'has_next_page' in page_info and page_info['has_next_page']:
                        params['page_info'] = page_info['next_page']
                    else:
                        break
                else:
                    _logger.info("Error:", response.status_code)
                    break
            if all_orders:
                orders = self.create_shopify_order(all_orders, shopify_instance_id, skip_existing_order, status='draft')
                return orders
            else:
                _logger.info("No draft orders found in Shopify.")
                return []

    def create_shopify_order(self, orders, shopify_instance_id, skip_existing_order, status):
        order_list = []
        for order in orders:
            if status == 'open':
                shopify_order_id = self.env['sale.order'].sudo().search([('order_shopify_id', '=', order.get('id'))],
                                                                        limit=1)
                if not shopify_order_id:
                    shopify_order_id = self.prepare_shopify_order_vals(shopify_instance_id, order, skip_existing_order)
            else:
                shopify_order_id = self.prepare_shopify_order_vals(shopify_instance_id, order, skip_existing_order)
            if shopify_order_id:
                order_list.append(shopify_order_id.id)
                shopify_order_id.name = order.get('name')
                if status == 'open':
                    shopify_order_id.name = order.get('name')
                    if shopify_order_id.state == 'draft':
                        shopify_order_id.action_confirm()
                # if status == 'open' or order.get('status') != 'open':
                #     if shopify_order_id.state == 'draft':
                #         shopify_order_id.action_confirm()
                #         self.env.cr.commit()
                #         inv = shopify_order_id._create_invoices()
                #         inv.action_post()
                # else:
                #     if shopify_order_id.invoice_status == 'to_invoice':
                #         inv = shopify_order_id._create_invoices()
                #         inv.action_post()

        return order_list

    def prepare_shopify_order_vals(self, shopify_instance_id, order, skip_existing_order):
        # call a method to check the customer is available or not
        # if not available create a customer
        # if available get the customer id
        # create a sale order
        # create a sale order line
        if order.get('customer'):
            res_partner = self.check_customer(order.get('customer'))
            if res_partner:
                res_partner.shopify_instance_id = shopify_instance_id.id
                shopify_order_id = self.env['sale.order'].sudo().search(
                    [('shopify_order_id', '=', order.get('id'))], limit=1)
                shopify_order_vals = {
                    'partner_id': res_partner.id,
                    'name': order.get('name'),
                    'shopify_instance_id': shopify_instance_id.id,
                    'shopify_order_id': order.get('id'),
                    'shopify_order_number': order.get('order_number'),
                    'shopify_order_status': order.get('status'),
                    'create_date': order.get('created_at'),
                    # 'shopify_order_date': draft_order.get('created_at'),
                    'shopify_order_total': order.get('total_price'),
                    'is_shopify_order': True,
                    'order_shopify_id': order.get('order_id'),
                }
                if not shopify_order_id:
                    shopify_order_id = self.sudo().create(shopify_order_vals)
                    shopify_order_id.state = 'draft'
                else:
                    if shopify_order_id and shopify_order_id.state == 'draft' and skip_existing_order == False:
                        shopify_order_id.sudo().write(shopify_order_vals)
                self.create_shopify_order_line(shopify_order_id, order, skip_existing_order, shopify_instance_id)

                return shopify_order_id

    def create_shopify_order_line(self, shopify_order_id, order, skip_existing_order, shopify_instance_id):
        amount = 0.00
        discount = 0.00
        if order.get('applied_discount'):
            amount = float(order.get('applied_discount').get('amount'))

        if len(order.get('line_items')) > 1:
            discount = amount / len(order.get('line_items'))
        else:
            discount = amount

        dict_tax = {}
        if shopify_order_id.state == 'draft':
            if shopify_order_id.order_line and skip_existing_order == False:
                shopify_order_id.order_line = [(5, 0, 0)]
            for line in order.get('line_items'):
                tax_list = []
                if line.get('tax_lines'):
                    for tax_line in line.get('tax_lines'):
                        dict_tax['name'] = tax_line.get('title')
                        if tax_line.get('rate'):
                            dict_tax['amount'] = tax_line.get('rate') * 100
                        tax = self.env['account.tax'].sudo().search([('name', '=', tax_line.get('title'))], limit=1)
                        if tax:
                            tax.sudo().write(dict_tax)
                        else:
                            tax = self.env['account.tax'].sudo().create(dict_tax)
                        if tax_line.get('price') != '0.00':
                            tax_list.append(tax.id)
                product = self.env['product.product'].search(['|', ('shopify_product_id', '=', line.get('product_id')),
                                                              ('shopify_variant_id', '=', line.get('variant_id'))],
                                                             limit=1)
                # if not product:
                #     product_vals = {
                #         'name' : line.get('title'),
                #         'shopify_variant_id': line.get('variant_id'),
                #     }
                #     product = self.env['product.product'].sudo().create(product_vals)
                if product:
                    subtotal = float(line.get('price')) * line.get('quantity')
                    shopify_order_line_vals = {
                        'order_id': shopify_order_id.id,
                        'product_id': product.id,
                        'name': line.get('title'),
                        'product_uom_qty': line.get('quantity'),
                        'price_unit': float(line.get('price')),
                        'discount': (discount / subtotal) * 100 if discount else 0.00,
                        'tax_id': [(6, 0, tax_list)]
                    }
                    shopify_order_line_id = self.env['sale.order.line'].sudo().create(shopify_order_line_vals)

            if order.get('shipping_line'):
                shipping = self.env['delivery.carrier'].sudo().search(
                    [('name', '=', order.get('shipping_line').get('title'))], limit=1)
                if not shipping:
                    delivery_product = self.env['product.product'].sudo().create({
                        'name': order.get('shipping_line').get('title'),
                        'detailed_type': 'product',
                    })
                    vals = {
                        'is_shopify': True,
                        'shopify_instance_id': shopify_instance_id.id,
                        'name': order.get('shipping_line').get('title'),
                        'product_id': delivery_product.id,
                    }
                    shipping = self.env['delivery.carrier'].sudo().create(vals)
                if shipping and shipping.product_id:
                    shipping_vals = {
                        'product_id': shipping.product_id.id,
                        'name': "Shipping",
                        'price_unit': float(order.get('shipping_line').get('price')),
                        'order_id': shopify_order_id.id,
                        'tax_id': [(6, 0, [])]
                    }
                    shipping_so_line = self.env['sale.order.line'].sudo().create(shipping_vals)

        return True

    def get_order_url(self, shopify_instance_id, endpoint):
        shop_url = "https://{}.myshopify.com/admin/api/{}/{}".format(shopify_instance_id.shopify_host,
                                                                     shopify_instance_id.shopify_version, endpoint)
        return shop_url

    def check_customer(self, customer):
        # check customer is available or not
        # if not available create a customer and pass it
        # if available write and pass the customer
        tags = customer.get('tags')
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
        if customer.get('first_name') and customer.get('last_name'):
            name = customer.get('first_name') + ' ' + customer.get('last_name')
        elif customer.get('first_name'):
            name = customer.get('first_name')
        else:
            name = customer.get('last_name')

        partner_obj = self.env['res.partner'].sudo().search(
            ['|', ('shopify_customer_id', '=', customer.get('id')), ('email', '=', customer.get('email'))],
            limit=1)
        if name:
            customer_vals = {
                'shopify_customer_id': customer.get('id'),
                'email': customer.get('email'),
                'name': name,
                'phone': customer.get('phone'),
                'shopify_note': customer.get('note'),
                'category_id': tag_list,
                'is_shopify_customer': True,
            }
            if not partner_obj:
                partner_obj = self.env['res.partner'].sudo().create(customer_vals)
            else:
                partner_obj.category_id = [(5, 0, 0)]
            # partner_obj.sudo().write(customer_vals)
        return partner_obj

    def import_shopify_orders(self, shopify_instance_ids, skip_existing_order, from_date, to_date):
        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for shopify_instance_id in shopify_instance_ids:
            self.import_shopify_draft_orders(shopify_instance_id, skip_existing_order, from_date, to_date)
            # import shopify oders from shopify to odoo
            # call method to connect to shopify

            all_orders = []
            url = self.get_order_url(shopify_instance_id, endpoint='orders.json')
            access_token = shopify_instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token
            }
            if from_date and to_date:
                params = {
                    "limit": 250,  # Adjust the page size as needed
                    "page_info": None,
                    "updated_at_min": from_date,
                    "updated_at_max": to_date,
                }
            else:
                params = {
                    "limit": 250,  # Adjust the page size as needed
                    "page_info": None
                }
            while True:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200 and response.content:
                    data = response.json()
                    orders = data.get('orders', [])
                    all_orders.extend(orders)

                    page_info = data.get('page_info', {})
                    if 'has_next_page' in page_info and page_info['has_next_page']:
                        params['page_info'] = page_info['next_page']
                    else:
                        break
                else:
                    _logger.info("Error:", response.status_code)
                    break
            if all_orders:
                orders = self.create_shopify_order(all_orders, shopify_instance_id, skip_existing_order, status='open')
                return orders
            else:
                _logger.info("No orders found in shopify")
                return []

    def export_orders_to_shopify(self, shopify_instance_ids, update):
        order_ids = self.sudo().browse(self._context.get("active_ids"))
        if not order_ids:
            if update == False:
                order_ids = self.sudo().search([('is_shopify_order', '=', False), ('is_exported', '=', False)])
            else:
                order_ids = self.sudo().search([])

        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for instance_id in shopify_instance_ids:
            url = self.get_order_url(instance_id, endpoint='draft_orders.json')
            access_token = instance_id.shopify_shared_secret

            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }

            response = ""
            for order in order_ids:
                line_val_list = []
                discount_val = []
                if order.order_line:
                    for line in order.order_line:
                        line_vals_dict = {
                            'title': line.product_id.name,
                            'price': line.price_unit,
                            'quantity': int(line.product_uom_qty),
                            "tax_lines": [],
                            "applied_discount": {
                                "description": "Custom discount",
                                "value_type": "percentage",
                                "value": line.discount,
                                "amount": line.price_unit - line.price_subtotal,
                                "title": "Custom"
                            }
                        }
                        line_val_list.append(line_vals_dict)
                        discount_val.append(line.discount)

                if order.is_shopify_order and order.shopify_instance_id.id == instance_id.id and update == True:

                    end = "draft_orders/{}.json".format(order.shopify_order_id)
                    url = self.get_order_url(instance_id, endpoint=end)
                    payload = {
                        "draft_order": {
                            "id": order.shopify_order_id,
                            "line_items": line_val_list,
                            "customer": {
                                "id": order.partner_id.shopify_customer_id
                            },
                            "tax_lines": [],
                        }
                    }
                    response = requests.put(url, headers=headers, data=json.dumps(payload))
                else:
                    if not order.is_shopify_order:
                        payload = {
                            "draft_order": {
                                "line_items": line_val_list,
                                "customer": {
                                    "id": order.partner_id.shopify_customer_id
                                },
                                "use_customer_default_address": True,
                                "tax_lines": [],
                            }
                        }

                        response = requests.post(url, headers=headers, data=json.dumps(payload))

                if response:
                    if response.content:
                        _logger.info(response.content)
                        draft_orders = response.json()
                        draft_order = draft_orders.get('draft_order', [])
                        if draft_order:
                            order.name = draft_order.get('name')
                            order.shopify_order_status = draft_order.get('status')
                            order.is_shopify_order = True
                            order.is_exported = True
                            order.shopify_order_id = draft_order.get('id')
                            _logger.info("Draft Order Created/Updated Successfully")
                    else:
                        _logger.info("Draft Order Creation/Updated Failed")
                        _logger.info("Failed", response.content)
                else:
                    _logger.info("Nothing Create / Updated")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    shopify_line_id = fields.Char("Shopify Line", copy=False)
    is_gift_card_line = fields.Boolean(copy=False, default=False)
