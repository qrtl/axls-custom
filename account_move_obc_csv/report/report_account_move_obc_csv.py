# Copyright 2021-2022 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveObcCsv(models.AbstractModel):
    _name = "report.account_move_obc_csv.report_obc_csv"
    _inherit = "report.report_csv.abstract"

    def _get_field_dict(self):
        field_dict = {
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
        return field_dict

    def _get_date(self, dt_date):
        """This method converts datetime to date in user's timezone."""
        return fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(dt_date)
        ).strftime("%Y%m%d")

    def _check_pickings(self, moves):
        invalid_moves = moves.filtered(
            lambda x: x.state in ("draft", "cancel", "done")
        )
        if invalid_moves:
            raise UserError(
                _(
                    "Following records are in invalid state (draft/done/cancel) for an "
                    "export.\n%s"
                )
                % ("\n".join(invalid_moves.mapped("name")))
            )
        exported_moves = moves.filtered(lambda x: x.is_exported)
        if exported_moves:
            raise UserError(
                _(
                    "Following records have been exported already. Please "
                    "unselect 'Exported' as necessary to export them again.\n%s"
                )
                % ("\n".join(exported_moves.mapped("name")))
            )

    # def _get_amounts(self, picking):
    #     amt_taxinc = amt_tax = 0.0
    #     for move in picking.move_lines:
    #         sale_line = move.sale_line_id
    #         amt_taxinc += move.product_uom_qty * sale_line.price_reduce_taxinc
    #         amt_tax += move.product_uom_qty * (
    #             sale_line.price_reduce_taxinc - sale_line.price_reduce_taxexcl
    #         )
    #     for sale_line in picking.sale_id.order_line:
    #         # For cash-on-delivery and delivery fees. We assume that there will
    #         # be no multiple deliveries for an order involving COD.
    #         if sale_line.product_id.default_code == "COD" or sale_line.is_delivery:
    #             amt_taxinc += sale_line.product_uom_qty * sale_line.price_reduce_taxinc
    #             amt_tax += sale_line.product_uom_qty * (
    #                 sale_line.price_reduce_taxinc - sale_line.price_reduce_taxexcl
    #             )
    #     return amt_taxinc, amt_tax

    def generate_csv_report(self, writer, data, pickings):
        self._check_pickings(pickings)
        today_date = self._get_date(fields.Datetime.now())
        writer.writeheader()
        field_dict = self._get_field_dict()
        item_num = 1
        for picking in pickings:
            warehouse = picking.picking_type_id.warehouse_id
            whs_partner = warehouse.partner_id
            company = picking.company_id
            order = picking.sale_id
            pick_create_date = self._get_date(picking.date)
            scheduled_date = self._get_date(picking.scheduled_date)
            partner_shipping = picking.partner_id
            carrier_code = (
                picking.yamato_carrier_code
                or partner_shipping.yamato_carrier_code
                or warehouse.yamato_carrier_code
            )
            if scheduled_date < today_date:
                raise UserError(
                    _("There is a delivery with a past scheduled date: %s")
                    % (picking.name)
                )
            # 伝票区分 '00' means that 送り状 will not be issued.
            slip_categ = "00"
            if carrier_code != "ZZZ01":
                slip_categ = "20" if order.is_cod else "10"
            amt_taxinc, amt_tax = self._get_amounts(picking)
            for move in picking.move_lines:
                vals = {
                    field_dict[2]: "1",  # Newly create
                    field_dict[3]: warehouse.yamato_shipper_code,
                    field_dict[4]: "10",
                    field_dict[5]: carrier_code,
                    field_dict[9]: "S001",
                    field_dict[10]: order.delivery_date
                    and order.delivery_date.strftime("%Y%m%d")
                    or "",
                    field_dict[12]: order.delivery_time_id
                    and order.delivery_time_id.delivery_time_categ
                    or "",
                    field_dict[13]: slip_categ,
                    field_dict[16]: int(amt_taxinc),
                    field_dict[17]: int(amt_tax),
                    field_dict[35]: self._get_sender_name(order, company, whs_partner),
                    field_dict[38]: whs_partner.zip if whs_partner else company.zip,
                    field_dict[39]: self._get_address(whs_partner or company),
                    field_dict[40]: whs_partner.phone if whs_partner else company.phone,
                    field_dict[45]: partner_shipping.name,
                    field_dict[47]: order.customer_contact or "",
                    field_dict[48]: partner_shipping.zip,
                    field_dict[49]: self._get_address(partner_shipping),
                    field_dict[50]: partner_shipping.phone,
                    field_dict[52]: scheduled_date,
                    field_dict[53]: today_date,
                    field_dict[54]: picking.name,
                    field_dict[59]: picking.name,
                    field_dict[60]: pick_create_date,
                    field_dict[61]: order.customer_order or "",
                    field_dict[72]: order.customer_order or "",
                    field_dict[104]: "1",  # Allow edit on screen
                    field_dict[105]: "0",
                    field_dict[106]: "1",  # Mewly create
                    field_dict[107]: item_num,
                    field_dict[108]: move.product_id.default_code,
                    field_dict[109]: "00",  # Fixed as 'bara'
                    field_dict[128]: int(move.product_uom_qty),
                }
                writer.writerow(vals)
                item_num += 1
            picking.is_exported = True

    def csv_report_options(self):
        res = super().csv_report_options()
        field_dict = self._get_field_dict()
        for _k, v in field_dict.items():
            res["fieldnames"].append(v)
        res["delimiter"] = ","
        res["quoting"] = csv.QUOTE_MINIMAL
        return res
