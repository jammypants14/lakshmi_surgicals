# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2024 ZestyBeanz Technologies(<http://www.zbeanztech.com>)
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
    'name': 'Document Property',
    'version': '18.0.0.4',
    'summary': 'Document Property',
    'description': """
            This module manages document property related features.
    """,
    'category':'Documents',
    'license': 'LGPL-3',
    'author': 'Zesty Beanz Technologies',
    'website': 'www.zbeanztech.com',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/document_property_views.xml',
        'views/document_village_views.xml',
        'views/sub_registrar_views.xml',
        'views/prior_deed_no_views.xml',
        'views/prior_deed_year_views.xml',
        'views/document_hypothecated_views.xml',
        ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}





