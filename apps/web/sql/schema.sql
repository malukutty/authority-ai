-- Created automatically on first use by lib/store.ts. Provided here for review / manual setup.

create table if not exists repeat_usage (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  ip_hash text not null,          -- salted SHA-256 of client IP; raw IP is never stored
  status text not null,           -- ok | error | mock
  model text not null,
  latency_ms integer not null
);
create index if not exists repeat_usage_created_idx on repeat_usage (created_at);

create table if not exists repeat_feedback (
  id uuid primary key,
  created_at timestamptz not null default now(),
  report_id text,
  example boolean not null default false,  -- feedback left on the fictional example report
  useful text,                    -- very | somewhat | not
  most_valuable text,
  missing text,
  use_again text,                 -- yes | maybe | no
  interview boolean not null default false,
  email text,                     -- only stored when consent = true
  consent boolean not null default false,
  intake jsonb                    -- only when the founder opts in to share their answers
);

-- Founders who agreed to an interview:
-- select created_at, email, useful, most_valuable, missing from repeat_feedback where interview order by created_at desc;
