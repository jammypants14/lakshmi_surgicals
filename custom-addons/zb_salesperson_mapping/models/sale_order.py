# -*- encoding: utf-8 -*-
from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.depends('order_line.sales_man_id')
    def _get_salesman(self):
        for rec in self:
            user_ids = []
            for line in rec.order_line:
                if line.sales_man_id:
                    user_ids.append(line.sales_man_id.id)
            rec.saleperson_ids = user_ids

    saleperson_ids = fields.Many2many('res.users', 'user_sale_rel', 'sale_id', 'user_id', string="Salesperson(s)",
                                      compute="_get_salesman", store=True)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sales_man_id = fields.Many2one('res.users', string="Salesman", copy=False)
    
    
    def _prepare_invoice_line(self, **optional_values):
        print("------------------------------executing")
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['salesman_id'] = self.sales_man_id and self.sales_man_id.id or False
        print("--------------salesman----------------", res['salesman_id'], res )
        return res