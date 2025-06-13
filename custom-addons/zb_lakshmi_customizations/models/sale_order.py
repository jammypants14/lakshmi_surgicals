from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"
   
    show_mrp = fields.Boolean(string="Show MRP in Reports")
    vendor_ids = fields.Many2many(
        'res.partner',
        compute='_compute_vendor_ids',
        string='Vendors',
        store=True
    )

    @api.depends('order_line.vendor_id')
    def _compute_vendor_ids(self):
        for order in self:
            vendors = order.order_line.mapped('vendor_id')
            order.vendor_ids = vendors
    
    def update_vendor(self):
        for rec in self:
            if rec.order_line:
               rec.order_line._onchange_product_id_get_vendor()
    
    @api.onchange('order_line')
    def _onchange_order_line_sl_no(self):
        for idx, line in enumerate(self.order_line, 1):
            line.sl_no = idx

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    sl_no = fields.Integer("Sl No.")
    vendor_id = fields.Many2one('res.partner', 'Vendor')
    
    @api.onchange('product_template_id')
    def _onchange_product_id_get_vendor(self):
        for line in self:
            line.vendor_id = False
            product = line.product_template_id
            if product.seller_ids:
                vendor = product.seller_ids[0].partner_id
                line.vendor_id = vendor

    
    