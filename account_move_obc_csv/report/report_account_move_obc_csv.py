# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class AccountMoveObcCsv(models.AbstractModel):
    _name = "report.account_move_obc_csv.report_obc_csv"
    _inherit = "report.report_csv.abstract"

    def _get_field_dict(self):
        labels = {
            1: "GL0010001",  # date
            2: "GL0012002",  # debit account
            3: "GL0012101",  # debit base amount
            4: "GL0013002",  # credit account
            5: "GL0013101",  # credit base amount
            6: "GL0010008",  # document number
            7: "GL0012001",  # debit department
            8: "GL0012003",  # debit sub-account
            9: "GL0012004",  # debit consumption tax categ
            10: "GL0012015",  # debit consumption tax rate type
            11: "GL0012005",  # debit consumption tax rate
            12: "GL0012009",  # debit partner code
            13: "GL0012012",  # debit project
            14: "GL0012102",  # debit consumption tax amount
            15: "GL0013001",  # credit department
            16: "GL0013003",  # credit sub-account
            17: "GL0013004",  # credit consumption tax categ
            18: "GL0013015",  # credit consumption tax rate type
            19: "GL0013005",  # credit consumption tax rate
            20: "GL0013009",  # credit partner code
            21: "GL0013012",  # credit project
            22: "GL0013102",  # credit consumption tax amount
            23: "GL0011001",  # remarks
        }
        return labels

    def _check_records(self, records):
        invalid_records = records.filtered(lambda x: x.state != "posted")
        if invalid_records:
            raise UserError(
                _(
                    "Following records are not in a valid state (posted) for export."
                    "\n%s"
                )
                % ("\n".join(invalid_records.mapped("name")))
            )
        exported_records = records.filtered(lambda x: x.is_exported)
        if exported_records:
            raise UserError(
                _(
                    "Following records have been exported already. Please "
                    "unselect 'Exported' as necessary to export them again.\n%s"
                )
                % ("\n".join(exported_records.mapped("name")))
            )

    def _get_report_vals_dict(self, record):
        labels = self._get_field_dict()
        vals_dict = defaultdict(dict)
        move_lines = record.line_ids.sorted(lambda x: abs(x.balance), reverse=True)
        first_debit, first_credit = True, True
        line_count = 1
        for line in move_lines:
            account_code, subaccount_code = "", ""
            if "." in account_code:
                account_code, subaccount_code = line.account_id.code.split(".")
            tax = line.tax_ids[:1]
            analytic_lines = line.analytic_line_ids
            project_line = analytic_lines.filtered(lambda x: x.plan_type == "project")[
                :1
            ]
            project_account = project_line.account_id
            first_line = False
            if (line.debit and first_debit) or (line.credit and first_credit):
                first_line = True
            line_num = 1 if first_line else line_count
            vals = vals_dict[1] if first_line else {}
            vals[labels[1]] = record.date
            vals[labels[6]] = record.name
            vals[labels[23]] = line.name
            if line.debit:
                vals[labels[2]] = account_code
                vals[labels[3]] = line.debit
                vals[labels[7]] = ""  # debit department
                vals[labels[8]] = subaccount_code or ""
                vals[labels[9]] = ""  # debit consumption tax categ
                vals[labels[10]] = ""  # debit consumption tax rate type
                vals[labels[11]] = (
                    tax and tax.amount or ""
                )  # debit consumption tax rate
                vals[labels[12]] = line.partner_id.ref or ""  # debit partner code
                vals[labels[13]] = project_account.name or ""
                vals[labels[14]] = ""  # debit consumption tax amount
                first_debit = False
            if line.credit:
                vals[labels[4]] = account_code or ""
                vals[labels[5]] = line.credit
                vals[labels[15]] = ""  # credit department
                vals[labels[16]] = subaccount_code or ""
                vals[labels[17]] = ""  # credit consumption tax categ
                vals[labels[18]] = ""  # credit consumption tax rate type
                vals[labels[19]] = (
                    tax and tax.amount or ""
                )  # credit consumption tax rate
                vals[labels[20]] = line.partner_id.ref or ""  # credit partner code
                vals[labels[21]] = project_account.name or ""
                vals[labels[22]] = ""  # credit consumption tax amount
                first_credit = False
            vals_dict[line_num] = vals
            line_count += 1
        return vals_dict

    def generate_csv_report(self, writer, data, records):
        self._check_records(records)
        writer.writeheader()
        for record in records:
            vals_dict = self._get_report_vals_dict(record)
            for _k, v in sorted(vals_dict.items()):
                writer.writerow(v)
            record.is_exported = True

    def csv_report_options(self):
        res = super().csv_report_options()
        field_dict = self._get_field_dict()
        for _k, v in field_dict.items():
            res["fieldnames"].append(v)
        res["delimiter"] = ","
        res["quoting"] = csv.QUOTE_MINIMAL
        return res
