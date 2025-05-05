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

from odoo import models, fields,api,_
from odoo.exceptions import ValidationError

class GSTEInvoiceBillWiz(models.TransientModel):
    _name = 'gst.einvoice.wizard'

    def action_submit(self):
        for record in self:
            active_id = self._context.get('active_id', [])
            invoice = self.env['account.move'].browse(active_id)
            if invoice.partner_id:
                if not invoice.partner_id.street and not invoice.partner_id.city:
                    raise ValidationError(_("Please Provide Customer's Street and City "))
                elif not invoice.partner_id.street :
                    raise ValidationError(_("Please Provide Customer's Street"))
                elif not  invoice.partner_id.city:
                    raise ValidationError(_("Please Provide Customer's City"))
                return invoice.generate_gst_einvoice_bill()
    
    
    def action_eway_submit(self):
        active_id = self._context.get('active_id', [])
        invoice = self.env['account.move'].browse(active_id)
        return invoice.generate_gst_ewaybill()
