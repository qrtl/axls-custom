This module adds a CSV import function to create new products and update existing ones based on
the data received from the PLM system. It also handles product revisions, allowing for tracking
of product changes over time.

Key features:
- Import products from CSV files with revision information
- Update existing products when new data is received
- Create new revisions when the revision number increases
- Track changes with detailed log notes
- Control product activation status through mapping configuration

This module depends on base_data_import and product_revision modules.
