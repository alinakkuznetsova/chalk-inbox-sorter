-- run this once in the supabase sql editor
create table if not exists public.inbox_log (
  id bigint generated always as identity primary key,
  message_id text not null unique,
  received_at timestamptz,
  from_email text,
  subject text,
  category text not null,
  priority text not null,
  summary text,
  model text,
  correct boolean,
  created_at timestamptz not null default now()
);

-- row level security on with no policies: only the service key (used by the sorter) can read or write
alter table public.inbox_log enable row level security;
