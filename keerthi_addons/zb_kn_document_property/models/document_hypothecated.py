from odoo import models, fields

class DocumentHypothecated(models.Model):
    _name = 'document.hypothecated'
    _description = 'Document Hypothecated'

    name = fields.Char(string='Name', required=True)
