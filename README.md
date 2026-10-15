# Chalk inbox sorter

An AI email triage system for [Chalk](https://findchalk.com), a London app for discovering local events. Every 15 minutes it reads new emails sent to hello@findchalk.com, asks an LLM to classify each one, gives it a colour-coded tag, flags anything urgent and logs the result to a database.

## Why I built it

I first built this as a no-code Zapier workflow for my jewellery brand, Parure London. It worked well, but multi-step automations need a paid Zapier plan. For Chalk I wanted the same result without a monthly bill, so I rebuilt it in Python. It now runs for free on GitHub Actions, and the only cost is a fraction of a penny per email in OpenAI usage.

## How it works

```
Zoho inbox ──Zoho Mail API──▶ sorter.py ──▶ OpenAI (gpt-4.1-mini) ──▶ category, priority, summary
                                    │
                                    ├──▶ Supabase: log every email
                                    ├──▶ every email: add its colour-coded category tag
                                    └──▶ urgent: flag it as important
```

Categories and tag colours: Venue Enquiries (yellow), Event Changes (pink), User Support (blue), Feedback and Bugs (orange), Partnerships and Press (green), Other (grey).

## Design decisions

- **Structured outputs.** The model must answer with JSON matching a schema, and the category can only be one of six fixed values. The Zapier version asked for a pipe-separated line and parsed it, which was more fragile.
- **Temperature 0.** Classification should be consistent, not creative.
- **Prompt injection.** Emails are untrusted input, so the prompt tells the model to treat the email purely as data and ignore any instructions inside it.
- **Tags, not folders.** The first version used IMAP and moved each email into a category folder, but an email can only live in one folder, so the inbox lost its overview. Tags give both: the inbox shows every email with a coloured tag, and clicking a tag in the sidebar shows just that category. IMAP cannot set Zoho tags, so the sorter now uses the Zoho Mail REST API with OAuth.
- **Idempotent.** Each email's Zoho message ID is checked against the log before processing, so an email is never classified or charged for twice, even if a run is repeated.
- **Log before acting.** The result is saved before the email is tagged, so a failure never loses track of an email.
- **HTML emails.** Markup and styles are stripped before the email reaches the model, and if the body cannot be fetched, Zoho's preview text is used instead. Bodies are capped at 2,000 characters to keep costs predictable.
- **Fails loudly.** If any email fails, the run exits with an error, so GitHub emails me.
- **Secrets stay secret.** All keys live in GitHub Actions secrets. Zoho access uses a refresh token that is swapped for a one-hour access token on every run. The Supabase table has row level security on with no public policies, so only the service key can touch it.

## Measuring accuracy

Every row in the `inbox_log` table has a `correct` column. I mark results true or false as I review them, and `evaluate.py` reports overall and per-category accuracy, so I can see where the prompt needs work rather than assuming it is right.

## Running it

1. Run `supabase/schema.sql` in the Supabase SQL editor.
2. Create a Self Client in the Zoho API Console (api-console.zoho.uk) and generate a grant code with the scopes `ZohoMail.accounts.READ,ZohoMail.folders.READ,ZohoMail.messages.ALL,ZohoMail.tags.ALL`, then exchange it for a refresh token.
3. Add these repository secrets in GitHub (Settings → Secrets and variables → Actions): `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`.
4. In the Actions tab, run **sort inbox** by hand with **dry run** ticked to check the classifications, then let the schedule take over.

To run locally: copy `.env.example` to `.env`, fill it in, then:

```
pip install -r requirements.txt
set -a && source .env && set +a
python sorter.py
```

Tests: `pip install pytest && pytest`. They also run automatically on every push.

## Stack

Python, Zoho Mail REST API (OAuth), OpenAI API with structured outputs, Supabase (PostgreSQL), GitHub Actions.
