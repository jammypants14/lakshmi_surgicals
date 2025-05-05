# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2024 ZestyBeanz Technologies.
#    (http://www.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Sales Hierarchy',
    'version': '18.0.0.0',
    'category': 'Sales',
    'sequence': 14,
    'summary': '',
    'description': """Sales Hierarchy""",
    'author': 'ZestyBeanz Technologies',
    'maintainer': 'ZestyBeanz Technologies',
    'support': 'support@zbeanztech.com',
    'website': 'http://www.zbeanztech.com/',
    'license': 'LGPL-3',
    'currency': 'USD',
    'price': 0.0,
    'depends': [
        'base'
    ],
    'data': [
        'views/res_users_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
