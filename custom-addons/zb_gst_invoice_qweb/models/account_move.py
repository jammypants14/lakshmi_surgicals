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

from odoo import fields, models, api
from num2words import num2words
import string

class AccountMove(models.Model):
    _inherit = 'account.move'


    delivery_address = fields.Text("Delivery Address")
    #po_date = fields.Date("PO/Ref Date")
    
    
    @api.onchange('partner_shipping_id')
    def onchange_partner_shipping_id_set_delivery_address(self):
        for rec in self:
            if rec.partner_shipping_id:
                rec.delivery_address = rec.partner_shipping_id._display_address()
    
    def get_delivery_address_formatted(self):
        address = self.delivery_address
        return address.split('\n')
    
    def get_tax_grouped(self):
        values = {}
        for rec in self:
            for line in rec.invoice_line_ids:
                val = {
                    'hsn_code': line.product_id.l10n_in_hsn_code,
                    'taxable_value': line.price_subtotal,
                    'line_tax': rec.currency_id.round(line.price_total - line.price_subtotal),
                }
                if line.igst_amount > 0:
                    val.update({
                        'cgst_rate': '',
                        'cgst_amt': line.cgst_amount,
                        'sgst_rate': '',
                        'sgst_amt': line.sgst_amount,
                        'igst_rate': line.tax_ids[0].amount if line.tax_ids else '',
                        'igst_amt': line.igst_amount,
                    })
                else:
                    value = []
                    if line.tax_ids:
                        for tax in line.tax_ids[0].children_tax_ids:
                            value.append(tax.amount)
                    val.update({
                        'cgst_rate': value[0] if value else '',
                        'cgst_amt': line.cgst_amount,
                        'sgst_rate': value[1] if len(value) > 1 else '',
                        'sgst_amt': line.sgst_amount,
                        'igst_rate': '',
                        'igst_amt': line.igst_amount,
                    })
                if line.product_id.l10n_in_hsn_code not in values:
                    values.update({line.product_id.l10n_in_hsn_code: val})
                else:
                    taxable_value = values[line.product_id.l10n_in_hsn_code].get('taxable_value', 0) + \
                                    val['taxable_value']
                    line_tax = values[line.product_id.l10n_in_hsn_code].get('line_tax', 0) + \
                                    val['line_tax']
                    cgst_amt = values[line.product_id.l10n_in_hsn_code].get('cgst_amt', 0) + val['cgst_amt']
                    sgst_amt = values[line.product_id.l10n_in_hsn_code].get('sgst_amt', 0) + val['sgst_amt']
                    igst_amt = values[line.product_id.l10n_in_hsn_code].get('igst_amt', 0) + val['igst_amt']
                    values[line.product_id.l10n_in_hsn_code].update({
                        'cgst_amt': cgst_amt,
                        'sgst_amt': sgst_amt,
                        'igst_amt': igst_amt,
                        'taxable_value': taxable_value,
                        'line_tax': line_tax,
                    })
            return list(values.values())
            
    
    def get_gst_tax(self,line):
        tax_list =[]
        join_tax =''
        if line:
            for tax in line:
                amount = ''
                if tax.amount > 0:
                    amount = str(float(tax.amount))
                elif tax.children_tax_ids:
                    amount = str(float(sum(tax.children_tax_ids.mapped('amount')))) 
                elif tax.amount == 0:  # Handle 0% tax
                    amount = '0'
                if amount:
                    amount = amount + ' %'
                    tax_list.append(amount)
                join_tax = ", ".join(tax_list)
        return join_tax            
    
    
    
    
 
