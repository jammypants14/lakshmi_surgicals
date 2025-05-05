#  -*- encoding: utf-8 -*-
#  OpenERP, Open Source Management Solution
#  Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    bank_details = fields.Html("Bank Details")
    l10n_in_gst_state_warning =  fields.Char(string="Manage Inventory in Route Sale")
    declaration = fields.Text("Declaration")


class Partner(models.Model):
    _inherit = "res.partner"
    
    l10n_in_gst_state_warning = fields.Char(string="Loading",default=False)
    