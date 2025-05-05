# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2025 ZestyBeanz Technologies(<http://www.zbeanztech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'GST E-Invoice and E-Way Bill',
    'version': '18.0.0.0.1',
    'summary': 'This module helps to generate e-way bills and e-invoices in compliance with Indian GST regulations.',
    'category':'Accounting',
    'website': 'http://www.zbeanztech.com/',
    'description': """
            This module helps to generate e-way bills and e-invoices in compliance with Indian GST regulations. .
    """,
    'author': 'ZestyBeanz Technologies',
    'maintainer': 'ZestyBeanz Technologies',
    'support': 'support@zbeanztech.com',
    'license': 'LGPL-3',
    'icon': "/zb_gst_einvoice_irn/static/description/icon.png",
    'images': ['static/description/banners/banner.png',],
    'currency': 'USD',
    'price': 10.0,
    'depends': ['base','account','l10n_in'],
    'data': [
            'security/ir.model.access.csv',
            'security/security.xml',
            'report/report.xml',
            'report/gst_invoice_qweb.xml',
            'report/gst_invoice_external_layout.xml',
            'wizard/gst_einvoice_wizard_view.xml',
            'wizard/custom_gst_invoice_views.xml',
            'view/account_invoice_view.xml',
            'view/res_partner_view.xml',
            'view/res_country_view.xml',
            'view/res_company_view.xml',
            'view/account_journal_view.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
