from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"
   
    show_mrp = fields.Boolean(string="Show MRP in Reports")
    
    @api.onchange('order_line')
    def _onchange_order_line_sl_no(self):
        for idx, line in enumerate(self.order_line, 1):
            line.sl_no = idx

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    sl_no = fields.Integer("Sl No.")