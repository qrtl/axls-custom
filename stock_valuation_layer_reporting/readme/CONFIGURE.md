## SVL Report Categories

1. Go to Inventory > Configuration > SVL Report Categories.
2. Create categories with:
   - Name
   - Sequence
   - Report Type (Storable/Consumable/Both)
   - Domain (stock.valuation.layer domain)
   - Other Category (set `is_other` for the fallback category)

## Other Category Behavior

1. Please assign Other Category to only one category (enforced by system).
2. If exactly one category matches, assign that category.
3. If multiple categories match, an error is logged and the first matching
   category (by sequence) is assigned.
4. If multiple categories match or none match, assign Other Category. If Other Category 
   is not defined, the report category will remain empty. Records with an empty report
   category will not be displayed in the SVL report.

## Product Category Configuration

For the valuation report, product categories must be marked for inclusion:

1. Go to Inventory > Configuration > Product Categories.
2. Open the desired product category.
3. Enable the "Include in SVL Report" option.