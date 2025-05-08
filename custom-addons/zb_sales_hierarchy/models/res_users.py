from odoo import models, fields, api


class ResUsers(models.Model):
    
    _inherit = 'res.users'
    _parent_name = 'reporting_to_id' 
    _parent_store = True
    
    reporting_to_id = fields.Many2one('res.users',string="Reporting To", index=True)
    parent_path = fields.Char(index=True)
    
