from odoo import models, fields,api
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    product_unit_cost = fields.Float(string="Cost", readonly=True)
       
    def _select(self) -> SQL:
        return SQL("""%s, 
        COALESCE(line.product_unit_cost, 0.0) AS product_unit_cost""",
                   super()._select())
