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

For each imported PLM record, the mappings of its item type are compared
with the category and the procure flag of the record. A mapping whose
categories or procure flags are set but do not match the record is not a
candidate. Among the candidates, the mapping with the highest score is
applied:

| Rank | Category       | Procure flag | Score |
|------|----------------|--------------|-------|
| 1    | Exact match    | Match        | 1.5   |
| 2    | Wildcard match | Match        | 1.25  |
| 3    | Exact match    | Not set      | 1     |
| 4    | Wildcard match | Not set      | 0.75  |
| 5    | Not set        | Match        | 0.5   |
| 6    | Not set        | Not set      | 0     |

- Exact match: one of the categories of the mapping equals the category
  of the record.
- Wildcard match: the category of the record matches one of the
  categories of the mapping as a pattern with `*` or `?`.
- Not set: the mapping has no category, or no procure flag. It matches
  any record.

The score is the sum of 1 for an exact category match (0.75 for a
wildcard match) and 0.5 for a procure flag match.

Two candidates share the highest score only when they have the same
rank. In that case, or when no mapping is a candidate, the record fails
with an error message that names the mappings, and no product is
created. Correct the mappings and import the record again. The order of
the lines in the list does not matter.

To configure the policy, go to *Data Import \> Data Import Settings \>
PLM-Product Mapping*.
