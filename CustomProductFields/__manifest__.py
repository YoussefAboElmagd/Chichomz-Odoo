{

    'name': 'Custom Product Fields',
    'version': '1.0.0.0.0',
    'summary': 'Custom Product Fields',
    'sequence': 30,
    'description': """
    Long Description of your modules""",
    'author': 'Odooistic',
    'company': 'Company Name',
    'website': 'https://www.website.com',
    'category': 'Customization',
    'depends': ['base','stock','product','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/tgrba.xml',
        'views/tgrbaa.xml',
    

   ],
    'application': True,
}