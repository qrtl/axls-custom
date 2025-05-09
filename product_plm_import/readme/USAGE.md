## Scheduled Jobs

There are three ir.cron records added by this module:

1.  PLM: Import PLM Products - The main cron job that imports PLM product
    records into Odoo in a periodical manner.
2.  PLM: Create products based on imported PLM records - A job that
    creates or updates products in Odoo based on the imported PLM records. Triggered
    by the main job.
3.  PLM: Send email notification on PLM data import - A job that sends
    email notifications to the relevant users. Triggered by the main job.
    Notification email is designed to be sent only once per the log
    record.

Alternatively, users can import PLM product records manually via
'Product PLM Import' wizard, which also triggers the last two jobs.

The status of an import log record becomes 'Done' when a product is
successfully created/updated or marked as 'Solved' for all the imported records.

## CSV Format

The CSV file should include the following columns:
- Part Number
- Name
- ESC ID
- Procure flag
- Item Type
- Category
- Unit of Material
- Description
- Spec
- Drawing No
- Generic Name
- Acceptance Test Category
- Rev (Revision number)

## Product Updates and Revisions

When importing a CSV file:

1. For new products (part numbers not found in the system):
   - A new product is created with all the information from the CSV
   - The product is set as active or inactive based on the mapping configuration
   - If a revision number is provided, a revision record is created

2. For existing products (part numbers already in the system):
   - The product information is updated with the new data from the CSV
   - A log note is added to the product with details of the changes
   - If the revision number in the CSV is greater than the current revision, a new revision is created

3. Log notes include:
   - The ECO file name (CSV file name)
   - Fields that were updated (showing old and new values)
   - Revision changes (e.g., Rev.1 to Rev.2)

These log notes provide a complete audit trail of changes made to products through the PLM import process.
