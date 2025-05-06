from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"
   
    vendor_reference = fields.Char(string="Vendor Reference", compute="get_reference", store=True)
    
    @api.depends('purchase_id.partner_ref')
    def get_reference(self):
        for rec in self:
            if rec.purchase_id:
                rec.vendor_reference = rec.purchase_id.partner_ref
            else:
                rec.vendor_reference = ''