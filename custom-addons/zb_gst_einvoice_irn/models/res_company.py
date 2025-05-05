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

from odoo import models, api, fields, _

class ResCompany(models.Model):
    _inherit= 'res.company'
    
    api_username = fields.Char("User Name")
    api_password = fields.Char("Password")
    ip_address = fields.Char("IP Address")
    api_client_id = fields.Char("Client ID")
    api_client_secret = fields.Char("Client Secret")
    api_auth_url = fields.Char("Auth URL")
    api_einvoice_url = fields.Char("E-Invoice Generate URL")
    api_gstin = fields.Char("Gstin")
    auth_token = fields.Char("Auth Token")
    eway_irn_generate_url = fields.Char("E-Way Bill Generate URL")
    eway_generate_url = fields.Char("E-Way Bill Generate URL")
    eway_username = fields.Char("User Name")
    eway_password = fields.Char("Password")
    eway_ip_address = fields.Char("IP Address")
    eway_gstin = fields.Char("Gstin")
    eway_client_id = fields.Char("Client ID")
    eway_client_secret = fields.Char("Client Secret")
    eway_auth_url = fields.Char("Auth URL")