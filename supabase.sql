-- Ejecutar en Supabase SQL Editor. Sustituir los DOS correos de ejemplo al final.
-- Solo los dos correos autorizados pueden leer y modificar las candidaturas.
create table if not exists public.allowed_emails (
 email text primary key check(email=lower(email))
);
revoke all on public.allowed_emails from anon, authenticated;

create table if not exists public.jobs (
 id uuid primary key default gen_random_uuid(),
 source text not null,
 source_id text not null,
 title text not null,
 company text not null default '',
 city text not null default '',
 url text not null,
 salary text,
 description text,
 published_at timestamptz,
 created_at timestamptz not null default now(),
 last_seen_at timestamptz not null default now(),
 status text not null default 'Pendiente' check (status in ('Pendiente','Guardada','Solicitada','Entrevista','Descartada')),
 favorite boolean not null default false,
 notes text not null default '',
 remote boolean not null default false,
 unique(source,source_id)
);
create index if not exists jobs_created_idx on public.jobs(created_at desc);
create schema if not exists private;
create or replace function private.is_allowed() returns boolean
language sql stable security definer set search_path = ''
as $$ select exists(select 1 from public.allowed_emails a where a.email=lower(auth.jwt()->>'email')) $$;
revoke all on function private.is_allowed() from public;
grant usage on schema private to authenticated;
grant execute on function private.is_allowed() to authenticated;
alter table public.allowed_emails enable row level security;
alter table public.jobs enable row level security;
drop policy if exists "shared_read" on public.jobs;
drop policy if exists "shared_insert" on public.jobs;
drop policy if exists "shared_update" on public.jobs;
drop policy if exists "shared_delete" on public.jobs;
create policy "shared_read" on public.jobs for select to authenticated using ((select private.is_allowed()));
create policy "shared_insert" on public.jobs for insert to authenticated with check ((select private.is_allowed()));
create policy "shared_update" on public.jobs for update to authenticated using ((select private.is_allowed())) with check ((select private.is_allowed()));
create policy "shared_delete" on public.jobs for delete to authenticated using ((select private.is_allowed()));
grant select,insert,update,delete on public.jobs to authenticated;
-- Lista permitida: sustituir antes de ejecutar.
insert into public.allowed_emails (email) values
 ('correo-de-lucia@ejemplo.com'),
 ('tu-correo@ejemplo.com')
on conflict (email) do nothing;
-- Activar Realtime para sincronización instantánea (si aún no existe).
do $$ begin
 if not exists (select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename='jobs') then
  alter publication supabase_realtime add table public.jobs;
 end if;
end $$;
