from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"
   
    show_mrp = fields.Boolean(string="Show MRP in Reports")