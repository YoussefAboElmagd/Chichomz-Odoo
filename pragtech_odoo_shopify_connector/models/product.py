# inherit class product.template and add fields for shopify instance and shopify product id
import base64
import json

import requests
from bs4 import BeautifulSoup
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config
config['limit_time_real'] = 10000000
import logging

_logger = logging.getLogger(__name__)


# inherit class product.product and add fields for shopify instance and shopify variant id

class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopify_variant_id = fields.Char('Shopify Variant Id')
    is_shopify_variant = fields.Boolean('Is Shopify Variant', default=False)
    shopify_barcode = fields.Char('Shopify Barcode')
    shopify_sku = fields.Char('Shopify SKU')
    shopify_price = fields.Float(string="Price")

    def _compute_product_price_extra(self):
        for product in self:
            if product.is_shopify_product:
                product.price_extra = product.shopify_price
            else:
                product.price_extra = sum(product.product_template_attribute_value_ids.mapped('price_extra'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopify_instance_id = fields.Many2one('shopify.instance', string='Shopify Instance')
    shopify_product_id = fields.Char('Shopify Product Id')
    shopify_product_status = fields.Char('Shopify Product Status')
    is_shopify_product = fields.Boolean('Is Shopify Product', default=False)
    shopify_barcode = fields.Char('Shopify Barcode')
    shopify_sku = fields.Char('Shopify SKU')
    shopify_image_ids = fields.One2many("shopify.product.image", "shopify_template_id")
    is_exported = fields.Boolean(string="Exported")

    def get_products_url(self, shopify_instance_id, endpoint):
        shop_url = "https://{}.myshopify.com/admin/api/{}/{}".format(shopify_instance_id.shopify_host,
                                                                     shopify_instance_id.shopify_version, endpoint)
        return shop_url

    def import_shopify_products(self, shopify_instance_ids, skip_existing_products, from_date, to_date):
        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for shopify_instance_id in shopify_instance_ids:
            url = self.get_products_url(shopify_instance_id, endpoint='products.json')
            access_token = shopify_instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token,
            }
            if from_date and to_date:
                params = {
                    "limit": 250,  # Adjust the page size as needed
                    "page_info": None,
                    "created_at_min": from_date,
                    "created_at_max": to_date,
                }
            else:
                params = {
                    "limit": 250,  # Adjust the page size as needed
                    "page_info": None,
                }
            all_products = []
            while True:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200 and response.content:
                    shopify_products = response.json()
                    products = shopify_products.get('products', [])
                    all_products.extend(products)
                    page_info = shopify_products.get('page_info', {})
                    if 'has_next_page' in page_info and page_info['has_next_page']:
                        params['page_info'] = page_info['next_page']
                    else:
                        break
                else:
                    break
            if all_products:
                products = self.create_products(all_products, shopify_instance_id, skip_existing_products)
                return products
            else:
                _logger.info("Products not found in shopify store")
                return []

    def create_products(self, products, shopify_instance_id, skip_existing_products):
        product_list = []
        for product in products:
            tags = product.get('tags')
            tag_list = []
            if tags:
                tags = tags.split(',')
                for tag in tags:
                    tag_id = self.env['product.tag'].sudo().search([('name', '=', tag)], limit=1)
                    if not tag_id:
                        tag_id = self.env['product.tag'].sudo().create({'name': tag})
                        tag_list.append(tag_id.id)
                    else:
                        tag_list.append(tag_id.id)
            description = False
            if product.get('body_html'):
                soup = BeautifulSoup(product.get('body_html'), 'html.parser')
                description_converted_to_text = soup.get_text()
                description = description_converted_to_text
            product_vals = {
                'name': product.get('title'),
                'shopify_product_id': product.get('id'),
                'is_shopify_product': True,
                "detailed_type": "product",
                'shopify_instance_id': shopify_instance_id.id,
                'default_code': product.get('sku') if product.get('sku') else '',
                'barcode': product.get('barcode') if product.get('barcode') else '',
                'shopify_barcode': product.get('barcode') if product.get('barcode') else '',
                'shopify_sku': product.get('sku') if product.get('sku') else '',
                'description_sale': description if description else False,
                'description': product.get(
                    'body_html') if product.get('body_html') else False,
                'taxes_id': [(6, 0, [])],
                'product_tag_ids': [(6, 0, tag_list)]
            }
            # #check if product is already imported or not
            product_id = self.env['product.template'].sudo().search(
                [('shopify_product_id', '=', product.get('id'))], limit=1)
            if not product_id:
                # create product in odoo
                product_id = self.env['product.template'].sudo().create(product_vals)
            else:
                if skip_existing_products == False:
                    product_id.sudo().write(product_vals)

            self.env.cr.commit()
            # getting attributes from the response
            if product.get('options'):
                dict_attr = {}
                for attr in product.get('options'):
                    product_attr = self.env['product.attribute'].sudo().search(
                        ['|', ('shopify_id', '=', attr.get('id')),
                         ('name', '=', attr.get('name'))], limit=1)
                    dict_attr['is_shopify'] = True
                    dict_attr['shopify_instance_id'] = shopify_instance_id.id
                    dict_attr['shopify_id'] = attr.get('id') if attr.get('id') else ''
                    dict_attr['name'] = attr.get('name') if attr.get('name') else ''
                    if not product_attr:
                        product_attr = self.env['product.attribute'].sudo().create(dict_attr)

                    pro_val = []
                    if attr.get('values'):
                        for value in attr.get('values'):
                            if value != 'Default Title':
                                existing_attr_value = self.env['product.attribute.value'].sudo().search(
                                    [('name', '=', value), ('attribute_id', '=', product_attr.id)], limit=1)
                                dict_value = {}
                                dict_value['is_shopify'] = True
                                dict_value['shopify_instance_id'] = shopify_instance_id.id
                                dict_value['name'] = value if value else ''
                                dict_value['attribute_id'] = product_attr.id

                                if not existing_attr_value and dict_value['attribute_id']:
                                    create_value = self.env['product.attribute.value'].sudo().create(
                                        dict_value)
                                    pro_val.append(create_value.id)
                                elif existing_attr_value:
                                    write_value = existing_attr_value.sudo().write(dict_value)
                                    pro_val.append(existing_attr_value.id)

                        if product_attr:
                            if pro_val:
                                exist = self.env['product.template.attribute.line'].sudo().search(
                                    [('attribute_id', '=', product_attr.id),
                                     ('value_ids', 'in', pro_val),
                                     ('product_tmpl_id', '=', product_id.id)], limit=1)
                                if not exist:
                                    exist = self.env['product.template.attribute.line'].sudo().create({
                                        'attribute_id': product_attr.id,
                                        'value_ids': [(6, 0, pro_val)],
                                        'product_tmpl_id': product_id.id
                                    })
                                else:
                                    exist.sudo().write({
                                        'attribute_id': product_attr.id,
                                        'value_ids': [(6, 0, pro_val)],
                                        'product_tmpl_id': product_id.id
                                    })
            sku = ''
            product_variant = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', product_id.id)])
            if product.get('variants'):
                list_2 = []
                for variant in product.get('variants'):
                    list_1 = []
                    if variant.get('option1') == 'Default Title' and product_id:
                        product_id.sudo().write({
                            'list_price': variant.get('price'),
                            'default_code': variant.get('sku'),
                            'weight': variant.get('weight'),
                            'shopify_sku': variant.get('sku'),
                            'barcode': variant.get('barcode'),
                            'shopify_barcode': variant.get('barcode'),
                        })
                        sku = variant.get('sku')

                    if variant.get('option1'):
                        list_1.append(variant.get('option1'))
                    if variant.get('option2'):
                        list_1.append(variant.get('option2'))
                    if variant.get('option3'):
                        list_1.append(variant.get('option3'))
                    for item in product_variant:
                        if item.product_template_attribute_value_ids:
                            list_values = []
                            for rec in item.product_template_attribute_value_ids:
                                list_values.append(rec.name)
                            if set(list_1).issubset(list_values):
                                # item.lst_price = variant.get('price')
                                item.default_code = variant.get('sku')
                                item.barcode = variant.get('barcode')
                                item.shopify_variant_id = variant.get('id')
                                item.shopify_instance_id = shopify_instance_id.id
                                item.is_shopify_product = True
                                item.shopify_barcode = variant.get('barcode')
                                item.shopify_sku = variant.get('sku')
                                item.weight = variant.get('weight')
                                item.taxes_id = [(6, 0, [])]
                                item.shopify_price = variant.get('price')
                                item.product_tmpl_id.list_price = 0.00
                                break

            if sku:
                product_id.default_code = sku
                product_id.shopify_sku = sku
            # if tag_list:
            #     product_id.product_tag_ids = [(6, 0, tag_list)]

            # syn product images
            if product.get('images'):
                for image in product.get("images", {}):
                    if image.get("src"):
                        shopify_image_id = str(image.get("id"))
                        url = image.get("src")
                        variant_ids = image.get("variant_ids")
                        position = image.get("position")
                        if not variant_ids:
                            # below method is used to sync simple product images.
                            shopify_product_images = self.sync_simple_product_images(shopify_image_id, url, product_id,position)
                        else:
                            # The below method is used to sync variable(variation) product images.
                            shopify_product_images = self.sync_variable_product_images(shopify_image_id, url,
                                                                                       variant_ids)
            product_list.append(product_id.id)
        return product_list

    def sync_simple_product_images(self, shopify_image_id, url, product_id,position):
        try:
            response = requests.get(url, stream=True, verify=True, timeout=90)
            if response.status_code == 200:
                image = base64.b64encode(response.content)
                if position == 1:
                    product_id.sudo().write({'image_1920': image})
                shopify_pdt_image = self.env['shopify.product.image'].sudo().search(
                    [('shopify_image_id', '=', shopify_image_id)], limit=1)
                image_vals = {
                    'shopify_image_id': shopify_image_id,
                    'shopify_image': image,
                    'shopify_template_id': product_id.id,
                    'url': url
                }
                if not shopify_pdt_image:
                    shopify_pdt_image = self.env['shopify.product.image'].sudo().create(image_vals)
                else:
                    shopify_pdt_image.sudo().write(image_vals)
        except Exception as error:
            pass

    def sync_variable_product_images(self, shopify_image_id, url, variant_ids):
        try:
            response = requests.get(url, stream=True, verify=True, timeout=90)
            if response.status_code == 200:
                image = base64.b64encode(response.content)
                for variant_id in variant_ids:
                    product_id = self.env['product.product'].sudo().search([('shopify_variant_id', '=', variant_id)])
                    product_id.sudo().write({'image_1920': image})
                    shopify_pdt_image = self.env['shopify.product.image'].sudo().search(
                        [('shopify_image_id', '=', shopify_image_id)], limit=1)
                    image_vals = {
                        'shopify_image_id': shopify_image_id,
                        'shopify_image': image,
                        'shopify_variant_id': product_id.id,
                        'shopify_template_id': product_id.product_tmpl_id.id,
                        'url': url
                    }
                    if not shopify_pdt_image:
                        shopify_pdt_image = self.env['shopify.product.image'].sudo().create(image_vals)
                    else:
                        shopify_pdt_image.sudo().write(image_vals)
        except Exception as error:
            pass

    def update_stock(self, shopify_instance_ids):
        location_ids = self.get_locations()
        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for shopify_instance_id in shopify_instance_ids:
            url = self.get_inventory_url(shopify_instance_id, endpoint='inventory_levels.json')
            access_token = shopify_instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token,
            }

            params = {
                "limit": 250,  # Adjust the page size as needed
                "page_info": None,
                "location_ids": location_ids
            }
            all_inventory_levels = []
            while True:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200 and response.content:
                    inv_levels = response.json()
                    levels = inv_levels.get('inventory_levels', [])
                    all_inventory_levels.extend(levels)
                    page_info = inv_levels.get('page_info', {})
                    if 'has_next_page' in page_info and page_info['has_next_page']:
                        params['page_info'] = page_info['next_page']
                    else:
                        break
                else:
                    break
            if all_inventory_levels:
                updated_products = self.update_product_stock(all_inventory_levels, shopify_instance_id)
                return updated_products
            else:
                _logger.info("Inventory Levels not found in shopify store")
                return []

    def get_inventory_url(self, shopify_instance_id, endpoint):
        shop_url = "https://{}.myshopify.com/admin/api/{}/{}".format(shopify_instance_id.shopify_host,
                                                                     shopify_instance_id.shopify_version, endpoint)
        return shop_url

    def update_product_stock(self, levels, shopify_instance_id):
        stock_inventory_obj = self.env["stock.quant"]
        stock_inventory_name_obj = self.env["stock.inventory.adjustment.name"]
        warehouse_id = self.env['stock.warehouse'].sudo().search([('id', '=', 1)], limit=1)

        product_list = []
        stock_inventory_array = {}
        product_ids_list = []
        for level in levels:
            end_url = "inventory_items/{}.json".format(level.get('inventory_item_id'))
            url = self.get_inventory_url(shopify_instance_id, endpoint=end_url)
            access_token = shopify_instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token,
            }
            params = {
                "limit": 250,  # Adjust the page size as needed
            }

            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200 and response.content:
                inv_item = response.json()
                item = inv_item.get('inventory_item', [])
                if item.get('sku'):
                    product = self.env['product.product'].sudo().search(
                        [('default_code', '=', item.get('sku'))], limit=1)
                    if product and level.get('available') != None and product not in product_ids_list:
                        stock_inventory_line = {
                            product.id: level.get('available'),
                        }
                        stock_inventory_array.update(stock_inventory_line)
                        product_ids_list.append(product)



                        # if level.get('available') != None:
                        #     res_product_qty = self.env['stock.change.product.qty'].sudo().search(
                        #         [('product_id', '=', product.id)], limit=1)

                        # dict_q = {}
                        # dict_q['new_quantity'] = level.get('available')
                        # dict_q['product_id'] = product.id
                        # dict_q['product_tmpl_id'] = product.product_tmpl_id.id
                        #
                        # if not res_product_qty:
                        #     create_qty = self.env['stock.change.product.qty'].sudo().create(dict_q)
                        #     create_qty.change_product_qty()
                        # else:
                        #     write_qty = res_product_qty.sudo().write(dict_q)
                        #     qty_id = self.env['stock.change.product.qty'].sudo().search(
                        #         [('product_id', '=', product.id)], limit=1)
                        #     if qty_id:
                        #         qty_id.change_product_qty()


                        product_list.append(product.id)
        inventory_name = 'Inventory For Instance "%s"' % (shopify_instance_id.name)
        inventories = stock_inventory_obj.create_inventory_adjustment_ept(stock_inventory_array,
                                                                          warehouse_id.lot_stock_id, True,
                                                                          inventory_name)
        return product_list

    def get_locations(self):
        locations = self.env['shopify.location'].sudo().search([('is_shopify', '=', True)])
        loc_ids = ','.join(str(loc.shopify_location_id) for loc in locations) if locations else ''
        return loc_ids

    def export_products_to_shopify(self, shopify_instance_ids, update):
        products_ids = self.sudo().browse(self._context.get("active_ids"))
        if not products_ids:
            if update == False:
                products_ids = self.sudo().search([('is_shopify_product', '=', False), ('is_exported', '=', False)],
                                                  limit=1)
            else:
                products_ids = self.sudo().search([])
        if shopify_instance_ids == False:
            shopify_instance_ids = self.env['shopify.instance'].sudo().search([('shopify_active', '=', True)])
        for instance_id in shopify_instance_ids:
            url = self.get_products_url(instance_id, endpoint='products.json')
            access_token = instance_id.shopify_shared_secret
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }

            response = ""
            for product in products_ids:
                tag_vals = ','.join(str(tag.name) for tag in product.product_tag_ids) if product.product_tag_ids else ''
                if product.is_shopify_product and product.shopify_instance_id.id == instance_id.id and update == True:
                    end = "products/{}.json".format(product.shopify_product_id)
                    url = self.get_products_url(instance_id, endpoint=end)
                    if not product.attribute_line_ids:
                        data = {
                            "product": {
                                "id": product.shopify_product_id,
                                "title": product.name,
                                'tags': tag_vals,
                                "variants": [
                                    {
                                        "title": "Default Title",
                                        "price": product.list_price,
                                        "sku": "",
                                        "position": 1,
                                        "option1": "Default Title",
                                        "option2": "",
                                        "option3": "",
                                        "barcode": product.barcode,
                                        "sku": product.default_code,
                                    }
                                ],
                                "options": [
                                    {
                                        "name": "Title",
                                        "position": 1,
                                        "values": [
                                            "Default Title"
                                        ]
                                    }
                                ],
                            }
                        }
                    else:
                        data = {
                            "product": {
                                "id": product.shopify_product_id,
                                "title": product.name,
                                'tags': tag_vals,
                            }
                        }
                    response = requests.put(url, headers=headers, data=json.dumps(data))
                else:
                    if product.is_shopify_product == False or not product.shopify_instance_id.id == instance_id.id:
                        option_list = []
                        if product.attribute_line_ids:
                            for attr in product.attribute_line_ids:
                                val_list = []
                                for val in attr.value_ids:
                                    val_list.append(val.name)
                                attr_vals = {
                                    "name": attr.attribute_id.name,
                                    "values": val_list
                                }
                                option_list.append(attr_vals)

                            product_variant_ids = self.env['product.product'].sudo().search(
                                [('product_tmpl_id', '=', product.id)])
                            if product_variant_ids:
                                variant_val_list = []
                                for variant in product_variant_ids:
                                    variant_val = {
                                        'option1': "",
                                        'option2': "",
                                        'option3': "",
                                        'price': "0.00"
                                    }
                                    if variant.product_template_variant_value_ids:
                                        count = 1
                                        for value in variant.product_template_variant_value_ids:
                                            if count == 1:
                                                variant_val['option1'] = value.name
                                            elif count == 2:
                                                variant_val['option2'] = value.name
                                            else:
                                                variant_val['option3'] = value.name
                                            count += 1
                                        variant_val['price'] = variant.lst_price
                                        variant_val_list.append(variant_val)
                                data = {
                                    "product": {
                                        "title": product.name,
                                        "body_html": product.description,
                                        "options": option_list,
                                        "variants": variant_val_list,
                                        "tags": tag_vals,
                                    }
                                }
                            else:
                                data = {
                                    "product": {
                                        "title": product.name,
                                        "body_html": product.description,
                                        "options": option_list,
                                        "tags": tag_vals,
                                    }
                                }
                        else:
                            data = {
                                "product": {
                                    "title": product.name,
                                    "body_html": product.description,
                                    "variants": [
                                        {
                                            "title": "Default Title",
                                            "price": product.list_price,
                                            "sku": "",
                                            "position": 1,
                                            "option1": "Default Title",
                                            "option2": "",
                                            "option3": "",
                                            "barcode": product.barcode,
                                            "sku": product.default_code,
                                        }
                                    ],
                                    "options": [
                                        {
                                            "name": "Title",
                                            "position": 1,
                                            "values": [
                                                "Default Title"
                                            ]
                                        }
                                    ],
                                    "tags": tag_vals,
                                    # "status": "draft"
                                }
                            }

                        json_data = json.dumps(data)
                        response = requests.post(url, headers=headers, data=json_data)

                if response:
                    if response.content:
                        _logger.info(response.content)
                        shopify_products = response.json()
                        product_res = shopify_products.get('product', [])
                        if product_res:
                            product.shopify_product_id = product_res.get('id')
                            product.is_shopify_product = True
                            product.shopify_instance_id = instance_id.id
                            product.is_exported = True
                            _logger.info("Product created/updated successfully")
                    else:
                        _logger.info("Product creation/updation failed")
                        _logger.info("Error message:", response.text)


# inherit class product.attribute and add fields for shopify
class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    is_shopify = fields.Boolean(string='Is Shopify?')
    shopify_instance_id = fields.Many2one('shopify.instance', string='Shopify Instance')
    shopify_id = fields.Char(string='Shopify Attribute Id')


# inherit class product.attribute.value and add fields for shopify
class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    is_shopify = fields.Boolean(string='Is Shopify?')
    shopify_instance_id = fields.Many2one('shopify.instance', string='Shopify Instance')
    shopify_id = fields.Char(string='Shopify Attribute Value Id')
