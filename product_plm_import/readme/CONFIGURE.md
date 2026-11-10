Update fields in the company (in the 'PLM I/F' tab):

- PLM Path: the absolute path to the PLM directory to fetch the files
  from.
- PLM Notification Body: the text will be included in the notification
  email body.
- PLM Notified Groups: assign groups to notify when a new file is
  fetched from the PLM.

The PLM-Product Mapping menu enables users to define product policies,
such as Product Type, Product Category, Routes, etc., which will be
applied to the product in Odoo. The values of item_type_id,
category_ids, and procure_flag_ids serve as keys to identify which
policy will be applied.

For each imported PLM record, the mappings of its item type are checked
against the category and the procure flag of the record:

- Category: 1 point when a category of the mapping equals the PLM
  category, 0.5 when it matches as a wildcard pattern (`*`, `?`), and 0
  when the mapping has no category.
- Procure flag: 1 point when a procure flag of the mapping equals the
  PLM procure flag, and 0 when the mapping has no procure flag.

A mapping with categories or procure flags that do not match the record
is not a candidate, even when the other part matches. Among the
candidates, the mapping with the highest total is applied.

When no mapping is a candidate, or two or more candidates share the
highest total, the record fails with an error message that names the
mappings, and no product is created. Correct the mappings so that one
mapping has the highest total, and import the record again. The order
of the lines in the list does not matter.

For example, for a PLM record with item type Mech, category Damper and
procure flag Buy:

- Categories Aluminum Panel and Damper, procure flag Buy: 2 points.
- No category, procure flag Buy: 1 point.
- No category, no procure flag: 0 points.
- Category Aluminum Panel, procure flag Buy: not a candidate.

The first mapping is applied. Without its procure flag, it would score 1
point, the same as the second mapping, and the record would fail.

To configure the policy, go to *Data Import \> Data Import Settings \>
PLM-Product Mapping*.
