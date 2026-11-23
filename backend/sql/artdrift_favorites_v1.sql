-- Art Drift only. Execute on a dedicated Supabase project AFTER user approves
-- its organization/cost and configures Google OAuth. Never reuse Anna's tables.
-- Data API privileges are deliberately separate from row-level authorization.
begin;

create table if not exists public.artdrift_favorites (
  user_id uuid not null references auth.users(id) on delete cascade,
  artwork_key text not null,
  is_favorite boolean not null default true,
  artwork_snapshot jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, artwork_key),
  constraint artdrift_favorites_key_valid
    check (char_length(artwork_key) <= 96
      and artwork_key ~ '^[a-z][a-z0-9_]{1,24}:[0-9]{1,12}$'),
  constraint artdrift_favorites_snapshot_valid
    check (artwork_snapshot is null or
      (jsonb_typeof(artwork_snapshot) = 'object'
       and pg_column_size(artwork_snapshot) <= 16384))
);

alter table public.artdrift_favorites enable row level security;
revoke all on table public.artdrift_favorites from anon;
-- Supabase projects may auto-grant TRUNCATE/TRIGGER/REFERENCES to authenticated.
-- RLS does not protect TRUNCATE, so remove ALL default table privileges first.
revoke all on table public.artdrift_favorites from authenticated;
grant select, insert, update on table public.artdrift_favorites
  to authenticated;
revoke delete on table public.artdrift_favorites from authenticated;

drop policy if exists artdrift_favorites_select_own
  on public.artdrift_favorites;
create policy artdrift_favorites_select_own
  on public.artdrift_favorites for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists artdrift_favorites_insert_own
  on public.artdrift_favorites;
create policy artdrift_favorites_insert_own
  on public.artdrift_favorites for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists artdrift_favorites_update_own
  on public.artdrift_favorites;
create policy artdrift_favorites_update_own
  on public.artdrift_favorites for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

comment on table public.artdrift_favorites is
  'Art Drift user-owned favorites only; deletion uses is_favorite=false tombstones.';
commit;
