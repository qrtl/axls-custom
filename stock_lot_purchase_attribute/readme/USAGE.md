Activate the scheduled action before clicking 'RUN MANUALLY' and
deactivate it after the process is finished. We need to activate it
because calling _trigger() for each batch of records only works with an
active cron job.
