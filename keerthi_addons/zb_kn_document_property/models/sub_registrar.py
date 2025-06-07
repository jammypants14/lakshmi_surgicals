from odoo import models, fields,api
class SubRegistrar(models.Model):
    _name = 'sub.registrar'
    _description = 'Sub Registrar'

    name = fields.Char(string='Sub Registrar Name', required=True)