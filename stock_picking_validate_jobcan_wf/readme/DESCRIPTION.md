This module intends to enforce checking of relevant Jobcan workflow status in validating
outgoing transfers that meet any of the following conditions:

- Involves owner stock in any of the stock move line
- Skip Jobcan Workflow is NOT selected

For the API configuration, follow the instructions provided by base_api_connection.

Refer to https://ssl.wf.jobcan.jp/api_doc for Jobcan WF API specification.

This module also adds functionality to automatically confirm stock picking workflows using a scheduled cron job and notifies assigned users of any validation failures via Odoo chat messages.

The cron job confirms stock pickings that meet the following conditions:
- The state is assigned.
- The Jobcan_wf_number is set.
- The status of the JobCan WF is finished
