from odoo import models, fields,api
class DocumentVillage(models.Model):
    _name = 'document.village'
    _description = 'Document Village'

    name = fields.Char(string='Village Name', required=True)