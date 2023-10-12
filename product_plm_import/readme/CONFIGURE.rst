Update fields in the company (in the 'PLM I/F' tab):

- PLM Path: the absolute path to the PLM directory to fetch the files from.
- PLM Notification Body: the text will be included in the notification email body.
- PLM Notified Groups: assign groups to notify when a new file is fetched from the PLM.

Users can specify field mappings generated from PLM to be applied to product fields in Odoo from PLM-Product Mapping menu.
In the PLM-Product Mapping menu, there are two rules available for applying purchase descriptions to the products:
- Standard Description: The purchase description will be generated using values from the Generic Name, Drawing No, and Spec fields, with the format: "Generic Name / Drawing No / Spec."
- PLM Description: The purchase description will be generated using the value from the description field of the plm.product model.
