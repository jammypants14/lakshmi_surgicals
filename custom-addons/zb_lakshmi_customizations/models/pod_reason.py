from odoo import api, fields, models, _

class PODReason(models.Model):
    _name = 'pod.reason'
    _description = 'POD Reason'
    
    name = fields.Char(string='Name')