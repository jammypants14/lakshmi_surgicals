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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cgst_amount = fields.Float("CGST Amount", compute="calculate_gst_amount")
    sgst_amount = fields.Float("SGST Amount", compute="calculate_gst_amount")
    igst_amount = fields.Float("IGST Amount", compute="calculate_gst_amount")
    label = fields.Char(string="Label")
    label_text = fields.Text(string="Label")
    lot_ids = fields.Many2many('stock.lot', string="Serial Number/Lot", store=True)

    @api.onchange('name')
    def _onchange_name_set_editable_label(self):
        #if not self.label:
        internal_ref = self.product_id.default_code or ''
        product_name = self.product_id.name or ''

        invoice = self.move_id
        sale_orders = self.env['sale.order'].search([('invoice_ids', 'in', invoice.ids)])
        stock_moves = sale_orders.mapped('picking_ids.move_ids_without_package')
        lots = stock_moves.filtered(lambda m: m.product_id == self.product_id).mapped('lot_ids')
        self.lot_ids = lots
        
        lines = []
        if internal_ref:
            lines.append(f"[{internal_ref}]")
        if product_name:
            lines.append(product_name)
        if lots:
            lines.append("Batch(s):")
            for lot in lots.sorted(key=lambda l: l.name):
                exp_date = lot.expiration_date or lot.use_date
                if exp_date:
                    exp_str = exp_date.strftime('%d/%m/%Y')
                    lines.append(f"{lot.name} - Exp: {exp_str}")
                else:
                    lines.append(f"{lot.name}")
        self.label = "\n".join(lines)
        self.label_text = "\n".join(lines)
        print("-------------------------", lots)

            
    
    @api.depends('price_subtotal', 'price_total','quantity','price_unit')
    def calculate_gst_amount(self):
        for rec in self:
            tax_amount = rec.price_total - rec.price_subtotal
            # print(self.company_id.state_id.name,rec.partner_id.state_id.name)
            if rec.partner_id.state_id.id == rec.company_id.state_id.id:
                rec.cgst_amount = rec.sgst_amount = tax_amount / 2
                rec.igst_amount = 0
            else:
                rec.cgst_amount = rec.sgst_amount = 0
                rec.igst_amount = tax_amount