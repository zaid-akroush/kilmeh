-- Kilmeh contribute-words: database schema and access rules.
-- SPDX-License-Identifier: Apache-2.0
--
-- Paste this whole file into the Supabase SQL editor once, on a fresh project.
-- Public API model: INSERT ONLY. The public (anon) role can add rows and can
-- never read, change or delete anything. Only the project owner (dashboard,
-- service role) can read the data.
--
-- The browser generates the contributor id (a UUID) and the deletion code itself,
-- so it never needs to read anything back (requests use Prefer: return=minimal).

begin;

-- ---------------------------------------------------------------------------
-- Shared text rule, in a schema the REST API does not expose.
--
-- text_ok(v, max_len, single_line) is true when v:
--   * is not null and has 1..max_len characters;
--   * has at least one visible character (not only whitespace, zero-width,
--     bidi or other format characters);
--   * does not start with = + - or @ (spreadsheet formula injection), even
--     behind leading whitespace, TAB, CR, LF or invisible format characters;
--   * for single-line fields, contains no TAB, CR or LF anywhere.
-- Nothing is stripped or rewritten: Arabic is stored exactly as sent.
-- INVISIBLE below is: [:space:], U+0085, U+00A0, U+00AD, U+034F, U+061C,
-- U+115F-U+1160, U+1680, U+180E, U+2000-U+200F, U+2028-U+202F, U+205F-U+2064,
-- U+2066-U+206F, U+2800, U+3000, U+3164, U+FE00-U+FE0F, U+FEFF, U+FFA0,
-- U+E0000-U+E007F.
-- Single-line fields also reject TAB, LF, VT, FF, CR, U+0085, U+2028 and U+2029.
-- ---------------------------------------------------------------------------

create schema kilmeh_private;
revoke all on schema kilmeh_private from public;
grant usage on schema kilmeh_private to anon;

create function kilmeh_private.text_ok(v text, max_len integer, single_line boolean)
returns boolean
language sql
immutable
parallel safe
as $fn$
    select v is not null
        and char_length(v) between 1 and max_len
        and v ~ '[^[:space:]\u0085\u00a0\u00ad\u034f\u061c\u115f-\u1160\u1680\u180e\u2000-\u200f\u2028-\u202f\u205f-\u2064\u2066-\u206f\u2800\u3000\u3164\ufe00-\ufe0f\ufeff\uffa0\U000e0000-\U000e007f]'
        and v !~ '^[[:space:]\u0085\u00a0\u00ad\u034f\u061c\u115f-\u1160\u1680\u180e\u2000-\u200f\u2028-\u202f\u205f-\u2064\u2066-\u206f\u2800\u3000\u3164\ufe00-\ufe0f\ufeff\uffa0\U000e0000-\U000e007f]*[=+@-]'
        and (not single_line or v !~ '[\t\n\v\f\r\u0085\u2028\u2029]')
$fn$;

revoke all on function kilmeh_private.text_ok(text, integer, boolean) from public;
grant execute on function kilmeh_private.text_ok(text, integer, boolean) to anon;

-- Country of the contributor's Arabic -> dialect group. The single SQL source of
-- truth for the mapping (the JS copy is COUNTRY_DIALECT in js/logic.js). Pure: it
-- reads no table. Unknown input gives NULL.
create function kilmeh_private.dialect_of(country text)
returns text
language sql
immutable
parallel safe
as $fn$
    select case country
        when 'JO' then 'levantine'
        when 'PS' then 'levantine'
        when 'SY' then 'levantine'
        when 'LB' then 'levantine'
        when 'IQ' then 'iraqi'
        when 'EG' then 'egyptian'
        when 'SD' then 'sudanese'
        when 'SA' then 'gulf'
        when 'AE' then 'gulf'
        when 'KW' then 'gulf'
        when 'QA' then 'gulf'
        when 'BH' then 'gulf'
        when 'OM' then 'gulf'
        when 'LY' then 'maghrebi'
        when 'TN' then 'maghrebi'
        when 'DZ' then 'maghrebi'
        when 'MA' then 'maghrebi'
        when 'MR' then 'maghrebi'
        when 'YE' then 'other'
        when 'SO' then 'other'
        when 'DJ' then 'other'
        when 'KM' then 'other'
        when 'other' then 'other'
    end
$fn$;

revoke all on function kilmeh_private.dialect_of(text) from public;
-- Needed because the generated column below is computed with the inserting role.
grant execute on function kilmeh_private.dialect_of(text) to anon;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table public.contributors (
    id uuid primary key,
    name text,
    email text,
    -- ISO 3166-1 alpha-2 code (uppercase) of the country whose Arabic the person
    -- speaks, or 'other'. Not where they live.
    country text not null,
    country_other text,
    -- Derived, never sent by the client: a stored generated column cannot be
    -- written by INSERT, so country and dialect can never disagree.
    dialect text not null generated always as (kilmeh_private.dialect_of(country)) stored,
    credit_by_name boolean not null default false,
    consent boolean not null,
    consent_text_version text not null,
    deletion_code text not null,
    created_at timestamptz not null default now(),

    constraint contributors_deletion_code_key unique (deletion_code),

    -- Name and email are optional. Empty or invisible-only strings are rejected:
    -- the client sends NULL instead.
    constraint contributors_name_check check (
        name is null or kilmeh_private.text_ok(name, 100, true)
    ),
    constraint contributors_email_check check (
        email is null
        or (
            kilmeh_private.text_ok(email, 254, true)
            and char_length(email) >= 3
            and email ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'
        )
    ),
    constraint contributors_country_check check (
        country in (
            'DZ', 'BH', 'KM', 'DJ', 'EG', 'IQ', 'JO', 'KW', 'LB', 'LY', 'MR',
            'MA', 'OM', 'PS', 'QA', 'SA', 'SO', 'SD', 'SY', 'TN', 'AE', 'YE', 'other'
        )
    ),
    constraint contributors_dialect_check check (
        dialect in ('levantine', 'gulf', 'egyptian', 'maghrebi', 'iraqi', 'sudanese', 'other')
    ),
    constraint contributors_country_other_check check (
        (country_other is null and country <> 'other')
        or (
            country = 'other'
            -- explicit NOT NULL: a CHECK that evaluates to NULL would pass
            and country_other is not null
            and kilmeh_private.text_ok(country_other, 100, true)
        )
    ),
    constraint contributors_credit_needs_name_check check (
        credit_by_name = false or name is not null
    ),
    constraint contributors_consent_check check (consent = true),
    constraint contributors_consent_version_check check (
        char_length(consent_text_version) between 1 and 32
        and consent_text_version ~ '^[A-Za-z0-9._-]+$'
    ),
    -- Format K-XXXXX-XXXXX, alphabet without 0, 1, I, L, O, U.
    constraint contributors_deletion_code_format_check check (
        deletion_code ~ '^K-[2-9A-HJKMNP-TV-Z]{5}-[2-9A-HJKMNP-TV-Z]{5}$'
    )
);

create table public.entries (
    id uuid primary key default gen_random_uuid(),
    -- NOT NULL plus the foreign key: an entry must point at an existing contributor.
    -- ON DELETE CASCADE: deleting a contributor deletes their entries too.
    contributor_id uuid not null references public.contributors (id) on delete cascade,
    word_id text not null,
    arabic text,
    arabizi text not null,
    arabic_feminine text,
    arabizi_feminine text,
    kept_in_english boolean not null default false,
    created_at timestamptz not null default now(),

    -- One answer per word per contributor: stops duplicate floods and double sends.
    constraint entries_contributor_word_key unique (contributor_id, word_id),

    constraint entries_word_id_check check (
        char_length(word_id) between 1 and 64 and word_id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'
    ),
    -- Arabic is required unless the contributor keeps the word in English.
    constraint entries_arabic_required_check check (kept_in_english or arabic is not null),
    constraint entries_arabic_check check (
        arabic is null or kilmeh_private.text_ok(arabic, 200, false)
    ),
    constraint entries_arabizi_check check (
        kilmeh_private.text_ok(arabizi, 200, false)
    ),
    constraint entries_arabic_feminine_check check (
        arabic_feminine is null or kilmeh_private.text_ok(arabic_feminine, 200, false)
    ),
    constraint entries_arabizi_feminine_check check (
        arabizi_feminine is null or kilmeh_private.text_ok(arabizi_feminine, 200, false)
    )
);

create index entries_contributor_id_idx on public.entries (contributor_id);

-- ---------------------------------------------------------------------------
-- Privileges: start from nothing, then grant INSERT on the client columns only.
-- Supabase grants ALL on new public tables to anon and authenticated by default,
-- so the revokes below are required, not decoration.
-- ---------------------------------------------------------------------------

revoke all on table public.contributors from public, anon, authenticated;
revoke all on table public.entries from public, anon, authenticated;

-- Column-level INSERT: the client cannot set created_at or the entry id.
-- No grant on dialect (generated) or created_at.
grant insert (
    id, name, email, country, country_other, credit_by_name,
    consent, consent_text_version, deletion_code
) on table public.contributors to anon;

grant insert (
    contributor_id, word_id, arabic, arabizi, arabic_feminine, arabizi_feminine,
    kept_in_english
) on table public.entries to anon;

-- ---------------------------------------------------------------------------
-- Row level security: on for both tables, one INSERT policy each for anon.
-- There is deliberately NO select, update or delete policy for anyone, so even
-- a stray grant could not expose or change rows through the public API.
-- ---------------------------------------------------------------------------

alter table public.contributors enable row level security;
alter table public.entries enable row level security;
alter table public.contributors force row level security;
alter table public.entries force row level security;

create policy contributors_anon_insert on public.contributors
    as permissive
    for insert
    to anon
    with check (
        consent = true
        and (name is null or kilmeh_private.text_ok(name, 100, true))
        and (
            email is null
            or (
                kilmeh_private.text_ok(email, 254, true)
                and char_length(email) >= 3
                and email ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'
            )
        )
        and country in (
            'DZ', 'BH', 'KM', 'DJ', 'EG', 'IQ', 'JO', 'KW', 'LB', 'LY', 'MR',
            'MA', 'OM', 'PS', 'QA', 'SA', 'SO', 'SD', 'SY', 'TN', 'AE', 'YE', 'other'
        )
        and (
            (country = 'other' and kilmeh_private.text_ok(country_other, 100, true))
            or (country <> 'other' and country_other is null)
        )
        and (credit_by_name = false or name is not null)
        and char_length(consent_text_version) between 1 and 32
        and deletion_code ~ '^K-[2-9A-HJKMNP-TV-Z]{5}-[2-9A-HJKMNP-TV-Z]{5}$'
    );

create policy entries_anon_insert on public.entries
    as permissive
    for insert
    to anon
    with check (
        contributor_id is not null
        and char_length(word_id) between 1 and 64
        and word_id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'
        and (kept_in_english or arabic is not null)
        and (arabic is null or kilmeh_private.text_ok(arabic, 200, false))
        and kilmeh_private.text_ok(arabizi, 200, false)
        and (arabic_feminine is null or kilmeh_private.text_ok(arabic_feminine, 200, false))
        and (arabizi_feminine is null or kilmeh_private.text_ok(arabizi_feminine, 200, false))
    );

commit;
