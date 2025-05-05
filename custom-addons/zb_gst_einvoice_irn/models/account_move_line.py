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

from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cgst_amount = fields.Float("CGST Amount", compute="calculate_gst_amount")
    sgst_amount = fields.Float("SGST Amount", compute="calculate_gst_amount")
    igst_amount = fields.Float("IGST Amount", compute="calculate_gst_amount")

    @api.depends('price_subtotal', 'price_total','quantity','price_unit')
    def calculate_gst_amount(self):
        for rec in self:
            tax_amount = rec.price_total - rec.price_subtotal
            if rec.partner_id.state_id.id == self.env.company.state_id.id:
                rec.cgst_amount = rec.sgst_amount = tax_amount / 2
                rec.igst_amount = 0
            else:
                rec.cgst_amount = rec.sgst_amount = 0
                rec.igst_amount = tax_amount