from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    product_unit_cost = fields.Float("Cost", compute='_compute_product_unit_cost', store=True)

    @api.depends('product_id')
    def _compute_product_unit_cost(self):
        for line in self:
            if line.product_id:
                cost = line.product_id.standard_price
                line.product_unit_cost = float(cost or 0.0)
            else:
                line.product_unit_cost = 0.0