This module adds functionality to automatically confirm stock picking workflows using a scheduled cron job. It integrates with Jobcan API to validate picking operations before confirmation.

This module execute confirm stock moves that following conditions automatically. 
 - State is assigned
 - Jobcan_wf_number is set
 - Status of JobCan WF is finished

JobCan API can be called 5,000 times in an hour.

## Features

- Automatically confirm stock pickings with `jobcan_wf_number` set.
- Validate pickings with Jobcan API before confirmation.
- Notify assigned users of any validation failures via Odoo chat messages.