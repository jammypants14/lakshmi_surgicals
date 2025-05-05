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
from urllib.parse import unquote_plus

from odoo import fields, models
import itertools
from odoo.tools import (
    SQL,
)


class GstReports(models.Model):
    _name = 'gst.reports'
    _description = 'Account GST Reports'

    name = fields.Char("Reference")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    report_type = fields.Selection([
        ('gstr1', 'GSTR1'),
        ('gstr2', 'GSTR2')
    ], "Type", default="gstr1")
    invoice_ids = fields.Many2many('account.move', 'invoice_gst_report_rel',
                                   'report_id', 'invoice_id', "Invoices")
    cancel_invoice_ids = fields.Many2many('account.move', 'invoice_gst_report_rel1',
                                   'report1_id', 'canceled_invoice_id', "Canceled Invoices")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    state = fields.Selection([
        ('not_uploaded', 'Not uploaded'),
        ('ready_to_upload', 'Ready to upload'),
    ], string='Status', default="not_uploaded")

    b2b_attachment_id = fields.Many2one('ir.attachment', "B2B CSV")
    b2b_nil_attachment_id = fields.Many2one('ir.attachment', "B2B Nil CSV")
    b2cs_attachment_id = fields.Many2one('ir.attachment', "B2CS CSV")
    export_attachment_id = fields.Many2one('ir.attachment', "Export CSV")
    cdnr_attachment_id = fields.Many2one('ir.attachment', "CDNR CSV")
    hsn_attachment_id = fields.Many2one('ir.attachment', "HSN CSV")
    json_attachment_id = fields.Many2one('ir.attachment', "Json")
    invoice_count_attachment_id = fields.Many2one('ir.attachment', "Invoice Count CSV")
    
    def action_set_prefix(self):
        for move in self.cancel_invoice_ids:
            if move.journal_id.gst_prefix_size:
                move.prefix_sequence = move.name[:move.journal_id.gst_prefix_size]
                move.prefix_number = move.name[move.journal_id.gst_prefix_size:]
            
        for move in self.invoice_ids:
            if move.journal_id.gst_prefix_size and len(move.name) > move.journal_id.gst_prefix_size:
                move.prefix_sequence = move.name[:move.journal_id.gst_prefix_size]
                move.prefix_number = move.name[move.journal_id.gst_prefix_size:]
            else:
                move.prefix_sequence = move.name
                move.prefix_number = ''

    def action_fetch_invoices(self):
        self.invoice_ids = False
        self.cancel_invoice_ids = False
        
        # For invoice_ids
        query = self.env['account.move']._where_calc(self.inv_search_domain())
        rows = self.env.execute_query(SQL("""
            SELECT id FROM account_move WHERE %(where_clause)s
            """,
            where_clause=query.where_clause or SQL("TRUE"),
        ))
        self.invoice_ids = [(6, 0, [x[0] for x in rows])]  # Use x[0] to access the first column
        
        # For cancel_invoice_ids
        query1 = self.env['account.move']._where_calc(self.inv_search2_domain())
        rows1 = self.env.execute_query(SQL("""
            SELECT id FROM account_move WHERE %(where_clause)s
            """,
            where_clause=query1.where_clause or SQL("TRUE"),
        ))
        self.cancel_invoice_ids = [(6, 0, [x[0] for x in rows1])]  # Use x[0] to access the first column
        
        self.state = 'ready_to_upload'

    def action_generate_csv(self):
        self.b2b_attachment_id = False
        self.b2b_nil_attachment_id = False
        self.b2cs_attachment_id = False
        self.export_attachment_id = False
        self.hsn_attachment_id = False
        self.cdnr_attachment_id = False
        self.json_attachment_id = False
        self.invoice_count_attachment_id = False
        self.env['csv.generator'].with_context({'report_id': self.id}).generate_all_csvs()

    def inv_search_domain(self):
        self.env.cr.execute("SELECT invoice_id FROM invoice_gst_report_rel")
        ignore_ids = [x[0] for x in self.env.cr.fetchall()]
        domain = [
            ('invoice_date', '>=', self.from_date),
            ('invoice_date', '<=', self.to_date),
            ('gst_status', '=', 'not_uploaded'),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
        ]
        if ignore_ids:
            domain.append(('id', 'not in', ignore_ids))
        if self.report_type == 'gstr1':
            domain.append(('move_type', 'in', ['out_invoice', 'out_refund']))
        elif self.report_type == 'gstr2':
            domain.append(('move_type', 'in', ['in_invoice', 'in_refund']))
        return domain
    
    def inv_search2_domain(self):
        self.env.cr.execute("SELECT invoice_id FROM invoice_gst_report_rel")
        ignore_ids = [x[0] for x in self.env.cr.fetchall()]
        domain = [
            ('invoice_date', '>=', self.from_date),
            ('invoice_date', '<=', self.to_date),
            ('gst_status', '=', 'not_uploaded'),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'cancel'),
        ]
        if ignore_ids:
            domain.append(('id', 'not in', ignore_ids))
        if self.report_type == 'gstr1':
            domain.append(('move_type', 'in', ['out_invoice', 'out_refund']))
        elif self.report_type == 'gstr2':
            domain.append(('move_type', 'in', ['in_invoice', 'in_refund']))
        return domain

    def export_b2b(self):
        if self.b2b_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.b2b_attachment_id.id,
                'target': 'new',
            }

    def export_b2b_nil(self):
        if self.b2b_nil_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.b2b_nil_attachment_id.id,
                'target': 'new',
            }

    def export_b2cs(self):
        if self.b2cs_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.b2cs_attachment_id.id,
                'target': 'new',
            }

    def export_export(self):
        for rec in self:
            if rec.export_attachment_id:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/%s?download=1' % rec.export_attachment_id.id,
                    'target': 'new',
                }

    def export_cdnr(self):
        if self.cdnr_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.cdnr_attachment_id.id,
                'target': 'new',
            }

    def export_hsn(self):
        if self.hsn_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.hsn_attachment_id.id,
                'target': 'new',
            }
            
    def export_invoice_count(self):
        if self.invoice_count_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.invoice_count_attachment_id.id,
                'target': 'new',
            }

    def export_json(self):
        if self.json_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=1' % self.json_attachment_id.id,
                'target': 'new',
            }

    @staticmethod
    def _unescape(text):
        try:
            return unquote_plus(text.encode('utf8'))
        except Exception:
            return text

    @staticmethod
    def get_tax_rate(line):
        tax_rate = 0
        for tax in line.tax_ids:
            if tax.tax_group_id.name == 'igst':
                tax_rate = tax.amount
            else:
                tax_rate += tax.amount
        return tax_rate

    def get_csv_data(self):
        data = {}
        b2cs_data = {}
        hsn_data = {}
        inv_count_dict = {}
        inv_count = 1
        inv_count_post = 0
        inv_count_cancel = 0
        for inv in self.invoice_ids:
            # HSN

            if inv.move_type == 'out_invoice' or inv.move_type == 'out_refund':
                for row in self.generate_hsn_rows(self, inv):
                    if row['hsn'] in hsn_data:
                        hsn_data[row['hsn']]['qty'] += row['qty']
                        hsn_data[row['hsn']]['value'] += row['value']
                        hsn_data[row['hsn']]['taxable'] += row['taxable']
                        hsn_data[row['hsn']]['ita'] += row['ita']
                        hsn_data[row['hsn']]['cta'] += row['cta']
                        hsn_data[row['hsn']]['sta'] += row['sta']
                    else:
                        hsn_data.update({
                            row['hsn']: {
                                'hsn': int(row['hsn']) - int(row['rate']),
                                'desc': row['desc'],
                                'uqc': row['uqc'],
                                'qty': row['qty'],
                                'value': row['value'],
                                'rate':row['rate'],
                                'taxable': row['taxable'],
                                'ita': row['ita'],
                                'cta': row['cta'],
                                'sta': row['sta'],
                                'cess': 0,
                            }
                        })

            # B2B
            if inv.invoice_type == 'b2b':
                if inv.amount_tax > 0.00:
                    rows = self.generate_b2b_rows(inv)
                    if 'b2b' in data:
                        data['b2b'].extend(rows)
                    else:
                        data.update({'b2b': rows})
                else:
                    rows = self.generate_b2b_nil_rows(inv)
                    if 'b2b_nil' in data:
                        data['b2b_nil']['intra_state_registered'] += rows[0]
                        data['b2b_nil']['intra_state_unregistered'] += rows[1]
                        data['b2b_nil']['inter_state_registered'] += rows[2]
                        data['b2b_nil']['inter_state_unregistered'] += rows[3]
                    else:
                        data.update({
                            'b2b_nil': {
                                "intra_state_registered": rows[0],
                                "intra_state_unregistered": rows[1],
                                "inter_state_registered": rows[2],
                                "inter_state_unregistered": rows[3],
                            }
                        })

            # B2CS
            elif inv.invoice_type == 'b2cs' and inv.amount_tax != 0.00:
                rows = self.generate_b2cs_rows(inv)
                for row in rows:
                    rate, pos = row['rate'], row['pos']
                    if pos in b2cs_data:
                        pos_grp = b2cs_data[pos]
                        if rate in pos_grp:
                            pos_grp[rate]['taxable'] += row['taxable']
                        else:
                            pos_grp.update({
                                rate: row
                            })
                    else:
                        b2cs_data.update({
                            pos: {
                                rate: row
                            }
                        })

            # CDNR
            if inv.move_type == 'out_refund' and inv.state == 'posted':
                if 'cdnr' in data:
                    data['cdnr'].append(self.generate_cdnr_rows(inv))
                else:
                    data.update({'cdnr': [self.generate_cdnr_rows(inv)]})

            # Export
            if inv.move_type == 'out_invoice' and inv.state == 'posted' and inv.partner_id.country_id and \
                    inv.partner_id.country_id.id != self.company_id.country_id.id:
                rows = self.generate_export_rows(inv)
                if 'export' in data:
                    data['export'].extend(rows)
                else:
                    data.update({'export': rows})
                    
        # INV COUNT
        for inv in (self.invoice_ids + self.cancel_invoice_ids).sorted(lambda x: (x.prefix_sequence and x.prefix_number), reverse=True):
            if inv.move_type == 'out_invoice' or inv.move_type == 'out_refund':
                prefix = inv.prefix_sequence
                rows = self.generate_invoice_count_rows(inv,prefix,inv_count_dict)

        if b2cs_data:
            rows = []
            for pos_grp in b2cs_data.values():
                for rate_grp in pos_grp.values():
                    rows.append([col for col in rate_grp.values()])
            data.update({'b2cs': rows})
        hsn_data = dict(sorted(hsn_data.items(), key=lambda item: item[1]["hsn"]))
        # print ([[col for col in x.values()] for x in hsn_data.values()])
        if hsn_data:
            data.update({'hsn': [[col for col in x.values()] for x in hsn_data.values()]})
        
        if inv_count_dict:
            prefix = list(inv_count_dict.keys())
            for line in prefix:
                prefix_sequences = self._findall_prefix_numbers(line)
                if not None in prefix_sequences:
                    missing_sequences = self.find_missing(prefix_sequences)
                    jumped_count=0
                    inv_count_dict[line].update({'jumped' :jumped_count})
                    if missing_sequences:
                        jumped_count=len(missing_sequences)
                        inv_count_dict[line].update({'jumped':jumped_count})
                        inv_count_dict[line]['inv_count'] += jumped_count
                        inv_count_dict[line].update({'missed_inv_series' : ';'.join([f'{line}-' + str(x) for x in missing_sequences])})
            data.update({'inv_count_dict': [[col for col in x.values()] for x in inv_count_dict.values()]})

        return data
    
    def findall_prefix_numbers(self, prefix):
        for rec in self:
            if prefix:
                domain = [
                    ('id', 'in', (self.invoice_ids + self.cancel_invoice_ids).ids),
                    ('company_id', '=', self.company_id.id),
                    ('prefix_sequence', '=', prefix)
                ]
                query = self.env['account.move']._where_calc(domain)
                rows = self.env.execute_query(SQL("""
                    SELECT DISTINCT account_move.prefix_number as prefix_number 
                    FROM account_move
                    WHERE %(where_clause)s
                    """,
                    where_clause=query.where_clause or SQL("TRUE"),
                ))
                
                # Extract prefix_number values from the result rows
                line_data = [row['prefix_number'] for row in rows]
                return line_data

    def find_missing(self,lst):
        return sorted(set(range(lst[0], lst[-1])) - set(lst))

    def generate_b2b_rows(self, inv):
        code = self._unescape(inv.partner_id.state_id.l10n_in_tin) or 0
        sname = self._unescape(inv.partner_id.state_id.name) or ''
        rate_grp = {}
        for line in inv.invoice_line_ids:
            rate = self.get_tax_rate(line)
            if rate in rate_grp:
                rate_grp[rate]['taxable'] += line.price_subtotal
            else:
                rate_grp.update({
                    rate: {
                        'gstin': inv.partner_id.vat,
                        'name': inv.partner_id.name,
                        'inv_name': inv.name,
                        'inv_date': inv.invoice_date.strftime('%d-%b-%Y'),
                        'inv_value': round(inv.amount_total, 2),
                        'pos': "{}-{}".format(code, sname),
                        'rev_chrg': 'N',
                        'tax_rate': 0,
                        'inv_type': 'regular',
                        'ecom_gstin': "",
                        'rate': round(rate, 2),
                        'taxable': round(line.price_subtotal, 2),
                        'cess': 0
                    }
                })
        return [[col for col in row.values()] for row in rate_grp.values()]

    def generate_b2b_nil_rows(self, inv):
        intra_state_registered = intra_state_unregistered = 0.00
        inter_state_registered = inter_state_unregistered = 0.00
        for line in inv.invoice_line_ids:
            if inv.partner_id.state_id.id != self.env.company.state_id.id:
                if inv.l10n_in_gstin:
                    inter_state_registered += round(line.price_subtotal, 2)
                else:
                    inter_state_unregistered += round(line.price_subtotal, 2)
            else:
                if inv.l10n_in_gstin:
                    intra_state_registered += round(line.price_subtotal, 2)
                else:
                    intra_state_unregistered += round(line.price_subtotal, 2)
        return [
            intra_state_registered, intra_state_unregistered,
            inter_state_registered, inter_state_unregistered
        ]

    def generate_b2cs_rows(self, inv):
        code = self._unescape(inv.partner_id.state_id.l10n_in_tin) or 0
        sname = self._unescape(inv.partner_id.state_id.name) or ''
        rate_grp = {}
        for line in inv.invoice_line_ids:
            rate = self.get_tax_rate(line)
            if rate in rate_grp:
                rate_grp[rate]['taxable'] += round(line.price_subtotal, 2)
            else:
                rate_grp.update({
                    rate: {
                        'type': 'OE',
                        'pos': "{}-{}".format(code, sname),
                        'tax_rate': 0,
                        'rate': round(rate, 2),
                        'taxable': round(line.price_subtotal, 2),
                        'cess': 0,
                        'gstin': ''
                    }
                })
        return [row for row in rate_grp.values()]

    @staticmethod
    def generate_hsn_rows(self, inv):
        data = {}
        sign = -1 if inv.move_type in ('out_refund', 'in_refund') else 1
        # 

        for line in inv.invoice_line_ids:
            hsn = line.product_id.l10n_in_hsn_code
            hsn_str = line.product_id.l10n_in_hsn_code
            rate = self.get_tax_rate(line)
            # if hsn == '30049011':
                # print (hsn_str, rate, 'sss\n')
            # print (rate)
            hsn = int(hsn_str) + int(rate) if hsn_str else False
            # print (hsn)
            # print (data[hsn])
            if hsn in data:
                data[hsn]['qty'] += (sign * line.quantity)
                data[hsn]['value'] += (sign * round(line.price_total, 2))
                data[hsn]['taxable'] += (sign * round(line.price_subtotal, 2))
                data[hsn]['ita'] += (sign * round(line.igst_amount, 2))
                data[hsn]['cta'] += (sign * round(line.cgst_amount, 2))
                data[hsn]['sta'] += (sign * round(line.sgst_amount, 2))
            else:
                # print (hsn,'ffffff')
                data.update({
                    hsn: {
                        'hsn': hsn,
                        'desc': line.product_id.l10n_in_hsn_warning,
                        'uqc': line.product_id.uom_id.l10n_in_code,
                        'qty': (sign * line.quantity),
                        'value': (sign * round(line.price_total, 2)),
                        'rate': round(rate, 2),
                        'taxable': (sign * round(line.price_subtotal, 2)),
                        'ita': (sign * round(line.igst_amount, 2)),
                        'cta': (sign * round(line.cgst_amount, 2)),
                        'sta': (sign * round(line.sgst_amount, 2)),
                       
                    }
                })
        # print (data,'dara')
        # print ([x for x in data.values()])
        return [x for x in data.values()]

    def generate_cdnr_rows(self, inv):
        rate = 0
        if inv.amount_untaxed > 0:
            rate = int(round((inv.amount_tax * 100) / inv.amount_untaxed))
        code = self._unescape(inv.partner_id.state_id.l10n_in_tin) or 0
        sname = self._unescape(inv.partner_id.state_id.name) or ''
        return [
            inv.partner_id.vat,
            inv.partner_id.name,
            "",
            "",
            inv.name,
            inv.invoice_date.strftime('%d-%b-%Y'),
            "N",
            "C",
            "{}-{}".format(code, sname),
            round(inv.amount_total, 2),
            0,
            round(rate, 2),
            round(inv.amount_untaxed, 2),
            0
        ]

    def generate_export_rows(self, inv):
        rate_grp = {}
        for line in inv.invoice_line_ids:
            rate = self.get_tax_rate(line)
            if rate in rate_grp:
                rate_grp[rate]['taxable'] += round(line.price_subtotal, 2)
            else:
                rate_grp.update({
                    rate: {
                        'type': "WOPAY",
                        'inv_name': inv.name,
                        'inv_date': inv.invoice_date.strftime('%d-%b-%Y'),
                        'inv_val': round(inv.amount_total, 2),
                        'port_code': inv.l10n_in_shipping_port_code_id.name or '',
                        'bill_no': "",
                        'bill_date': "",
                        'tax': 0,
                        'rate': round(rate, 2),
                        'taxable': round(line.price_subtotal, 2),
                    }
                })
        return [[col for col in row.values()] for row in rate_grp.values()]
    
    
    # def generate_invoice_count_rows(self, inv,prefix,inv_count_dict):
    #     if inv.move_type == 'out_invoice':
    #         document_nature = 'Invoices for outward supply'
    #     elif inv.move_type == 'out_refund':
    #         document_nature = 'Credit Notes for Outward Supply'
    #     else:
    #         return inv_count_dict 
    #
    #     if prefix:
    #         if prefix in inv_count_dict:
    #             inv_count_dict[prefix]['inv_count'] += 1
    #             inv_count_dict[prefix]['inv_from'] = inv.name if inv.name else ''
    #             inv_count_dict[prefix]['inv_count_post'] += 1 if inv.state == 'posted' else 0
    #             inv_count_dict[prefix]['inv_count_cancel'] += 1 if inv.state == 'cancel' else 0
    #         else:
    #             inv_count_cancel = inv_count_post = 0
    #             if inv.state == 'posted':
    #                 inv_count_post = 1 
    #             else:
    #                 inv_count_cancel = 1 
    #             inv_count_dict.update({prefix :
    #                 {
    #                     'inv_note' : document_nature,
    #                     'inv_from': inv.name,
    #                     'inv_to': inv.name,
    #                     'inv_count': 1,
    #                     'inv_count_post': inv_count_post,
    #                     'inv_count_cancel': inv_count_cancel,
    #                 }
    #             })
    #     return inv_count_dict
    
    def generate_invoice_count_rows(self, inv,prefix,inv_count_dict):
        # regex = re.compile(prefix)
        # if(re.match(regex, inv.name)):
        if prefix:
            if prefix in inv_count_dict:
                inv_count_dict[prefix]['inv_count'] += 1
                inv_count_dict[prefix]['inv_from'] = inv.name if inv.name else ''
                inv_count_dict[prefix]['inv_count_post'] += 1 if inv.state == 'posted' else 0
                inv_count_dict[prefix]['inv_count_cancel'] += 1 if inv.state == 'cancel' else 0
            else:
                inv_count_cancel = inv_count_post = 0
                if inv.state == 'posted':
                  inv_count_post = 1 
                else:
                  inv_count_cancel = 1 
                inv_count_dict.update({prefix :
                    {
                        'inv_note' : 'Invoices for outward supply',
                        'inv_from': inv.name,
                        'inv_to': inv.name,
                        'inv_count': 1,
                        'inv_count_post': inv_count_post,
                        'inv_count_cancel': inv_count_cancel,
                    }
                })
            return inv_count_dict
