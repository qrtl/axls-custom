/** @odoo-module **/

import {AnalyticDistribution} from "@analytic/components/analytic_distribution/analytic_distribution";
import {patch} from "web.utils";
import {useState} from "@odoo/owl";

patch(AnalyticDistribution.prototype, "custom.analytic_distribution.patch", {
    setup() {
        this._super(...arguments);
        this.relatedAccountIDs = useState([]);
    },

    async onSelect(option, params, tag) {
        await this._super(option, params, tag);
        const res = await this.orm.call(
            "ir.model",
            "search_read",
            [[["model", "=", this.props.record.resModel]]],
            {fields: ["apply_analytic_distribution_filter"], limit: 1}
        );
        this._applyFilter = Boolean(
            res.length && res[0].apply_analytic_distribution_filter
        );
        if (!this._applyFilter) return;
        const selectedIds = this.existingAnalyticAccountIDs;
        if (selectedIds.length) {
            const relatedRecords = await this.orm.call(
                "account.analytic.account",
                "read",
                [selectedIds, ["related_account_ids"]]
            );
            const relatedIds = [].concat(
                ...relatedRecords.map((r) => r.related_account_ids || [])
            );
            this.relatedAccountIDs.splice(0);
            this.relatedAccountIDs.push(...relatedIds);
        }
    },

    async deleteTag(id, fromGroup) {
        await this._super(id, fromGroup);
        if (!this.existingAnalyticAccountIDs.length) {
            this.relatedAccountIDs.splice(0);
            return;
        }
        const relatedRecords = await this.orm.call("account.analytic.account", "read", [
            this.existingAnalyticAccountIDs,
            ["related_account_ids"],
        ]);
        const newRelated = [].concat(
            ...relatedRecords.map((r) => r.related_account_ids || [])
        );
        this.relatedAccountIDs.splice(0);
        this.relatedAccountIDs.push(...newRelated);
    },

    analyticAccountDomain(groupId = null) {
        const domain = this._super(groupId);
        if (this.relatedAccountIDs.length) {
            domain.push(["id", "in", this.relatedAccountIDs]);
        }
        return domain;
    },
});
