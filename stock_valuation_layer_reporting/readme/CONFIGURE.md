Configuration

1. Go to Inventory > Configuration > SVL Report Categories.
2. Create categories with:
   - Name
   - Sequence
   - Display Type (Storable/Consumable/Both)
   - Domain (stock.valuation.layer domain)
   - Other Category (set `is_other` for the fallback category)

Other Category behavior

1. Please assign Other Category to only one category.
2. If exactly one report category matches, assign that category; otherwise 
   (if multiple or none match), assign Other Category.
3. If Other Category is not defined, the report category will remain empty in the above 
“otherwise” cases. Records with an empty report category will not be displayed in the 
SVL report.