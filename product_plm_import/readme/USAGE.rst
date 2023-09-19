There are three ir.cron records added by this module:

#. PLM: Import PLM Products
   The main cron job that imports PLM product records into Odoo in a periodical manner.
#. PLM: Create products based on imported PLM records
   A job that creates products in Odoo based on the imported PLM records. Triggerd by
   the main job.
#. PLM: Send email notification on PLM data import
   A job that sends email notifications to the relevant users. Triggerd by the main job.
   Notification email is designed to be sent only once per the log record.

Alternatively, users can import PLM product records manually via 'Product PLM Import'
wizard, which also triggers the last two jobs.

The status of an import log record becomes 'Done' when a product is successfully created
or marked as 'Solved' for all the imported records.
