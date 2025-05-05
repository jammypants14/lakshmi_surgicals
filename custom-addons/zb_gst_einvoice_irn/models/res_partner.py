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

from odoo import api, fields, models,_

class Partner(models.Model):
    _inherit = 'res.partner'
             
    transporter_id_num = fields.Char(string='Transporter ID')
    transporter_type = fields.Selection([('R', 'Regular')], string="Transporter Type")
     
    @api.constrains('vat', 'country_id')
    def check_vat(self):
        if self.env.context.get('no_vat_validation'):
            return

        for partner in self:
            country = partner.commercial_partner_id.country_id
            if partner.vat:
                if self._run_vat_test(partner.vat, country, partner.is_company) == True:
                    partner_label = _("partner [%s]", partner.name)
                    msg = partner._build_vat_error_message(country and country.code.lower() or None, partner.vat, partner_label)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: