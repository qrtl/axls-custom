Configuration

1. Go to Inventory > Configuration > SVL Report Categories.
2. Create categories with:
   - Name
   - Sequence
   - Display Type (Storable/Consumable/Both)
   - Domain (stock.valuation.layer domain)
   - Other Category (set `is_other` for the fallback category)

Other category behavior

1. Please assign Other category to only one category.
2. If exactly one category matches a record, that category is assigned.
3. If multiple categories match a record, the Other category is assigned.
4. If no categories match a record, the Other category is assigned.
5. If the Other category is not set, the report category remains empty in
   the above conditions. Records with an empty report category will not be displayed
   in the SVL report.
