# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class AccountMoveObcCsv(models.AbstractModel):
    _name = "report.account_move_obc_csv.report_obc_csv"
    _inherit = "report.report_csv.abstract"

    def _get_fields(self):
        return [
            "GL0010001",  # date
            "GL0012002",  # debit account
            "GL0012101",  # debit base amount
            "GL0013002",  # credit account
            "GL0013101",  # credit base amount
            "GL0010008",  # document number
            "GL0012001",  # debit department
            "GL0012003",  # debit sub-account
            "GL0012004",  # debit consumption tax categ
            "GL0012015",  # debit consumption tax rate type
            "GL0012005",  # debit consumption tax rate
            "GL0012007",  # debit consumption tax auto calc
            "GL0012009",  # debit partner code
            "GL0012012",  # debit project
            "GL0012102",  # debit consumption tax amount
            "GL0013001",  # credit department
            "GL0013003",  # credit sub-account
            "GL0013004",  # credit consumption tax categ
            "GL0013015",  # credit consumption tax rate type
            "GL0013005",  # credit consumption tax rate
            "GL0013007",  # credit consumption tax auto calc
            "GL0013009",  # credit partner code
            "GL0013012",  # credit project
            "GL0013102",  # credit consumption tax amount
            "GL0011001",  # remarks
        ]

    def _get_field_map(self):
        return {
            "account": {"dr": "GL0012002", "cr": "GL0013002"},
            "base_amount": {"dr": "GL0012101", "cr": "GL0013101"},
            "department": {"dr": "GL0012001", "cr": "GL0013001"},
            "subaccount": {"dr": "GL0012003", "cr": "GL0013003"},
            "tax_categ": {"dr": "GL0012004", "cr": "GL0013004"},
            "tax_rate_type": {"dr": "GL0012015", "cr": "GL0013015"},
            "tax_rate": {"dr": "GL0012005", "cr": "GL0013005"},
            "tax_auto_calc": {"dr": "GL0012007", "cr": "GL0013007"},
            "partner": {"dr": "GL0012009", "cr": "GL0013009"},
            "project": {"dr": "GL0012012", "cr": "GL0013012"},
        }

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

    def _get_move_department(self, record):
        """Regard the first department identified as the department of the journal
        entry.
        """
        department = self.env["account.analytic.account"].browse()
        for analytic_line in record.line_ids.analytic_line_ids:
            if analytic_line.plan_type == "department":
                department = analytic_line.account_id
                break
        return department

    def _update_vals(self, vals, line, move_department, drcr):
        account_code = line.account_id.code
        subaccount_code = ""
        if "." in account_code:
            # maxsplit=1 - we assume that an account code should contain only one
            # period (".") at most.
            account_code, subaccount_code = account_code.split(".", 1)
        # We assume that there should be only one project/department per journal
        # item if any.
        project = line.analytic_line_ids.filtered(
            lambda x: x.plan_type == "project"
        ).account_id[:1]
        if line.account_id.account_type in ("asset_receivable", "liability_payable"):
            department_name = move_department.code or ""
        else:
            department = line.analytic_line_ids.filtered(
                lambda x: x.plan_type == "department"
            ).account_id[:1]
            department_name = department.code or "0000"
        tax = line.tax_ids[:1]
        fields = self._get_field_map()
        vals[fields["account"][drcr]] = account_code
        vals[fields["base_amount"][drcr]] = line.debit if drcr == "dr" else line.credit
        vals[fields["department"][drcr]] = department_name
        vals[fields["subaccount"][drcr]] = subaccount_code or ""
        vals[fields["tax_categ"][drcr]] = (
            tax.obc_tax_category or line.tax_line_id.obc_tax_category or ""
        )
        vals[fields["tax_rate_type"][drcr]] = (
            tax.obc_tax_rate_type or line.tax_line_id.obc_tax_rate_type or ""
        )
        vals[fields["tax_rate"][drcr]] = tax.amount or line.tax_line_id.amount or ""
        vals[fields["tax_auto_calc"][drcr]] = 0  # No tax calculation
        vals[fields["partner"][drcr]] = line.partner_id.ref or ""
        vals[fields["project"][drcr]] = project.code or ""
        return vals

    def _get_report_vals_dict(self, record):
        accounting_date = record.date.strftime("%Y/%m/%d")
        move_department = self._get_move_department(record)
        # Sort lines so that the tax line(s) will come at the end of a journal entry
        move_lines = record.line_ids.filtered(lambda x: not x.tax_line_id).sorted(
            lambda x: abs(x.balance), reverse=True
        )
        move_lines += record.line_ids.filtered(lambda x: x.tax_line_id)
        vals_dict = defaultdict(dict)
        first_debit, first_credit = True, True
        line_count = 1
        purchase_line = record.stock_move_id.purchase_line_id
        for line in move_lines:
            first_line = False
            if (line.debit and first_debit) or (line.credit and first_credit):
                first_line = True
            line_num = 1 if first_line else line_count
            vals = vals_dict[1] if first_line else {}
            vals["GL0010001"] = accounting_date
            vals["GL0010008"] = record.name
            remarks = line.name
            if purchase_line:
                # This adjustment is so that the accounting staff can easily find
                # the related journal items for receipts based on the same string
                # set on those for vendor bill lines.
                remarks = "%s: %s, %s" % (
                    purchase_line.order_id.name,
                    purchase_line.name,
                    line.name,
                )
            vals["GL0011001"] = remarks
            if line.debit:
                vals = self._update_vals(vals, line, move_department, "dr")
                first_debit = False
            if line.credit:
                vals = self._update_vals(vals, line, move_department, "cr")
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
        fields = self._get_fields()
        for field in fields:
            res["fieldnames"].append(field)
        res["delimiter"] = ","
        res["quoting"] = csv.QUOTE_MINIMAL
        return res
