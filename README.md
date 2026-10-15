# Chalk inbox sorter

An AI email triage system for [Chalk](https://findchalk.com), a London app for discovering local events. Every 15 minutes it reads new emails sent to hello@findchalk.com, asks an LLM to classify each one, files it into the right folder, flags anything urgent and logs the result to a database.

## Why I built it

I first built this as a no-code Zapier workflow for my jewellery brand, Parure London. It worked well, but multi-step automations need a paid Zapier plan. For Chalk I wanted the same result without a monthly bill, so I rebuilt it in Python. It now runs for free on GitHub Actions, and the only cost is a fraction of a penny per email in OpenAI usage.

## How it works

```
Zoho inbox ──IMAP──▶ sorter.py ──▶ OpenAI (gpt-4.1-mini) ──▶ category, priority, summary
                         │
                         ├──▶ Supabase: log every email
                         ├──▶ urgent: flag it and keep it in the inbox
                         └──▶ everything else: move it into its category folder
```

Categories: Venue Enquiries, Event Changes, User Support, Feedback and Bugs, Partnerships and Press, Other.

## Design decisions

- **Structured outputs.** The model must answer with JSON matching a schema, and the category can only be one of six fixed values. The Zapier version asked for a pipe-separated line and parsed it, which was more fragile.
- **Temperature 0.** Classification should be consistent, not creative.
- **Prompt injection.** Emails are untrusted input, so the prompt tells the model to treat the email purely as data and ignore any instructions inside it.
- **Triage, not just labelling.** Urgent emails stay in the inbox and are flagged; everything else is filed away. The inbox only holds what needs attention now.
- **Idempotent.** Each email's Message-ID is checked against the log before processing, so an email is never classified or charged for twice, even if a run is repeated.
- **Log before acting.** The result is saved before the email is moved, so a failure never loses track of an email.
- **Emails stay unread.** Messages are fetched with `BODY.PEEK`, so the sorter never marks anything as read.
- **HTML-only emails.** Plain text is preferred; if an email only has HTML, the tags and styles are stripped before it reaches the model. Bodies are capped at 2,000 characters to keep costs predictable.
- **Fails loudly.** If any email fails, the run exits with an error, so GitHub emails me.
- **Secrets stay secret.** All keys live in GitHub Actions secrets. The Supabase table has row level security on with no public policies, so only the service key can touch it.

## Measuring accuracy

Every row in the `inbox_log` table has a `correct` column. I mark results true or false as I review them, and `evaluate.py` reports overall and per-category accuracy, so I can see where the prompt needs work rather than assuming it is right.

## Running it

1. Run `supabase/schema.sql` in the Supabase SQL editor.
2. Add these repository secrets in GitHub (Settings → Secrets and variables → Actions): `EMAIL_ADDRESS`, `EMAIL_PASSWORD` (a Zoho app password), `IMAP_HOST`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`.
3. In the Actions tab, run **sort inbox** by hand with **dry run** ticked to check the classifications, then let the schedule take over.

To run locally: copy `.env.example` to `.env`, fill it in, then:

```
pip install -r requirements.txt
set -a && source .env && set +a
python sorter.py
```

Tests: `pip install pytest && pytest`. They also run automatically on every push.

## Stack

Python, IMAP (Zoho Mail), OpenAI API with structured outputs, Supabase (PostgreSQL), GitHub Actions.
