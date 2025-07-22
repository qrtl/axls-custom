To enable the filter for a specific model

1.  Go to **Settings → Technical → Database Structure → Models**.
2.  Open the model where you want the analytic distribution filter.
3.  Enable **Apply Analytic Distribution Filter**.

To define related accounts (used by the filter)

1.  Go to **Invoicing → Configuration → Analytic Distribution
    Accounts**.
2.  Open the analytic account and add its related accounts in the
    **Related Accounts** table.
    - If no related accounts are set, the widget falls back to standard
      (unfiltered) behavior.

## Example

You have two plans, each with two accounts:

- **Plan A**: Account A, Account B
- **Plan B**: Account C, Account D

For **Account A**, add this in the *Related Accounts* table: - Plan B →
Account D

**Result:** When you select **Account A** (Plan A) in the
analytic_distribution field, only **Account D** will be available for
Plan B.
