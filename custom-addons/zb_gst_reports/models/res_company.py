#  -*- encoding: utf-8 -*-
#  OpenERP, Open Source Management Solution
#  Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from odoo import models
from odoo.tools import (
    SQL,
)

class ResCompany(models.Model):
    _inherit = 'res.company'

    def set_invoice_gst_types(self):
        # B2B
        query = self.env['account.move']._where_calc([
            ('l10n_in_gstin', '!=', False),
            ('partner_id.vat', '!=', False),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ])
        self.env.execute_query(SQL("""
            UPDATE account_move SET invoice_type = 'b2b' 
            WHERE %(where_clause)s
            """,
            where_clause=query.where_clause or SQL("TRUE"),
        ))
    
        # B2CS
        query = self.env['account.move']._where_calc([
            '&', '|', ('l10n_in_gstin', '=', False), ('partner_id.vat', '=', False),
            '&', ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
        ])
        self.env.execute_query(SQL("""
            UPDATE account_move SET invoice_type = 'b2cs' 
            WHERE %(where_clause)s
            """,
            where_clause=query.where_clause or SQL("TRUE"),
        ))
    
        # Export
        query = self.env['account.move']._where_calc([
            ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
            ('partner_id.country_id.id', '!=', False),
            ('partner_id.country_id.id', '!=', self.country_id.id),
        ])
        self.env.execute_query(SQL("""
            UPDATE account_move SET invoice_type = 'export' 
            WHERE %(where_clause)s
            """,
            where_clause=query.where_clause or SQL("TRUE"),
        ))
    
        # CDNR
        query = self.env['account.move']._where_calc([
            ('move_type', '=', 'out_refund'), ('state', '=', 'posted')
        ])
        self.env.execute_query(SQL("""
        UPDATE account_move SET invoice_type = 'cdnr' 
        WHERE %(where_clause)s
            """,
            where_clause=query.where_clause or SQL("TRUE"),
        ))