{
    'name': "product vendor",
    'version': '1.0',
    'depends': ['sale'],
    'author': "Author Name",
    'category': 'Category',
    'description': """
    Connect Odoo With TurboEx System API
    """,
    "depends": ["sale", "account", "base" , "stock","shopify_ept" ],
    "data": [
             
             "views/product_template.xml",
             
            ],
}