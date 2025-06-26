from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    product_unit_cost = fields.Float("Cost", related="product_template_id.standard_price")
   

    
    