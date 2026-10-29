create table public.registrations (
  id uuid primary key default gen_random_uuid(),
  event_slug text not null default 'avivamiento-mexicano',
  full_name text not null,
  age integer not null check (age between 1 and 120),
  sex text not null,
  email text not null,
  phone text not null,
  location text not null,
  church text not null,
  church_location text not null,
  pastor text not null,
  ministry text not null,
  consent boolean not null default false,
  status text not null default 'registered' check (status in ('registered', 'confirmed', 'cancelled')),
  created_at timestamptz not null default now(),
  unique (event_slug, email)
);

alter table public.registrations enable row level security;

create policy "Anyone can register with consent"
  on public.registrations
  for insert
  to anon
  with check (consent = true);