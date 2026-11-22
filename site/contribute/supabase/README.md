# Supabase setup for the contribute-words site

The site stores contributions in a Supabase (hosted Postgres) project. The public
page can only **insert** rows. It can never read, update or delete anything, so a
visitor (or anyone holding the public key) cannot see other people's names, emails
or words. Only the project owner can read the data, from the Supabase dashboard.

Until `config.js` exists, the site runs in **test mode**: it shows a "test mode,
nothing is sent" banner and only logs submissions to the browser console. Adding
`?mock=1` to the URL forces test mode even when `config.js` exists.

## One-time setup (board)

1. **Create the project.** Sign in at supabase.com, create an organization if
   needed, then **New project**. Name it `kilmeh-contribute`. Set a strong
   database password and store it in your password manager (it is not needed by the
   site). Pricing plan: Free.
2. **Region.** Pick an EU region, for example **Central EU (Frankfurt)**. It is close
   to the Middle East and North Africa and keeps the data under EU (GDPR) rules.
   Check the current region list when you create the project (**verify**).
3. **Create the tables.** Open **SQL Editor**, click **New query**, paste the whole
   of [`schema.sql`](schema.sql) and click **Run**. It should finish with "Success.
   No rows returned". Run it once only, on a fresh project.
4. **Check the rules took effect.** In **Table Editor**, both `contributors` and
   `entries` should show "RLS enabled". In **Authentication > Policies** each table
   has exactly one policy, an `INSERT` policy for `anon`. There must be no `SELECT`,
   `UPDATE` or `DELETE` policy.
5. **Copy the URL and public key.** Open **Project Settings > API** (or **Data API**
   and **API Keys**, depending on the dashboard version). Copy:
   - the **Project URL**, `https://<project-ref>.supabase.co`;
   - the **anon / public** key (legacy, a long `eyJ...` string) or the
     **publishable** key (`sb_publishable_...`). Either works.

   **Never copy the `service_role` or secret key** into the site or anywhere in the
   repo. It bypasses every rule above.
6. **Create `config.js`.** In `site/contribute/`, copy `config.example.js` to
   `config.js` and paste the two values. `config.js` is git-ignored on purpose.
   The anon key is public by design (every visitor's browser receives it), but
   keeping it out of git means the repo never holds environment settings.
7. **Allow the browser to reach your project.** In `index.html`, in the
   `Content-Security-Policy` meta tag, replace `https://YOUR-PROJECT-REF.supabase.co`
   with your Project URL. Without this the browser blocks the request.
8. **Test.** Serve the folder (`python3 -m http.server` inside `site/contribute/`),
   open `http://localhost:8000/`, complete 10 words, then check **Table Editor >
   entries** shows 10 new rows. Delete the test rows afterwards (see below).

### Publishing on GitHub Pages

GitHub Pages only serves committed files, and `config.js` is not committed. Two
options: commit `config.js` only on the branch Pages publishes from (not `main`),
or have a deploy workflow write `config.js` from a repository variable at build
time. That deploy step is not part of this change.

## Exporting the data as CSV

- Quick: **Table Editor**, open `entries` (or `contributors`), then **Export > Export
  to CSV**.
- One file with the words, country and dialect group, without names or emails (good for the
  public dataset): run this in **SQL Editor**, then **Download CSV**:

  ```sql
  select e.word_id, e.arabic, e.arabizi, e.arabic_feminine, e.arabizi_feminine,
         e.kept_in_english, c.country, c.country_other, c.dialect,
         case when c.credit_by_name then c.name end as credit_name,
         e.created_at
  from entries e
  join contributors c on c.id = e.contributor_id
  order by e.word_id, c.dialect, c.country;
  ```

**Opening an export safely.** The file holds text typed by strangers. The database
rejects free-text values whose first visible character is `=`, `+`, `-` or `@`
(also when hidden behind spaces, tabs, line breaks or invisible bidi, zero-width or
filler characters), which blocks the common spreadsheet formula injection. Still:

- **Never double-click the CSV** to open it in Excel, Numbers or LibreOffice.
- Open it in a text editor, or **import** it (Excel: Data > From Text/CSV; Google
  Sheets: File > Import; LibreOffice: the import dialog) and set **every column to
  Text** before loading, with UTF-8 encoding so the Arabic stays intact.
- Never publish the `email` column.

## Deleting a person's data on request

People ask for deletion by sending their **deletion code** (shown on the thank-you
screen, format `K-XXXXX-XXXXX`). Do this in the Supabase **SQL Editor**, which runs
as the default `postgres` role. Do not change the role selector.

0. **Check the role can delete (BYPASSRLS).** Row level security is *forced* on both
   tables, so a role without the `BYPASSRLS` attribute sees no rows and deletes nothing,
   **without an error** ("Success. No rows returned" with 0 rows affected). Run:

   ```sql
   select rolname, rolbypassrls from pg_roles where rolname = current_user;
   ```

   `rolbypassrls` must be `true`. The dashboard's `postgres` role is expected to have
   it on Supabase, but **confirm this on the live project** before the first real
   request. If it shows `false`, stop and ask the maintainers; do not disable RLS.

1. **Count before.** Replace `<code>` and run:

   ```sql
   select count(*) as contributors_before from contributors where deletion_code = '<code>';
   ```

   It must return **1**. If it returns 0, check the code with the person (codes never
   contain 0, 1, I, L, O or U).

2. **Delete.** Run both statements together:

   ```sql
   delete from entries where contributor_id = (select id from contributors where deletion_code = '<code>');
   delete from contributors where deletion_code = '<code>';
   ```

   The result for the second statement must report **1 row affected** ("DELETE 1").
   If it reports 0, nothing was deleted: go back to step 0. The foreign key also
   cascades, so the contributor delete alone removes the entries; the first
   statement is kept for clarity.

3. **Count after.** The contributor row existed before (step 1 returned 1, step 2
   said DELETE 1) and now both numbers must be 0:

   ```sql
   select
     (select count(*) from contributors where deletion_code = '<code>') as contributors_left,
     (select count(*) from entries e
        where not exists (select 1 from contributors c where c.id = e.contributor_id)) as orphan_entries;
   ```

4. Reply to the person that their data was deleted.

If someone gave an email and has lost the code, look them up by email instead and
confirm the request came from that address, then use the code found:

```sql
select id, deletion_code, created_at from contributors where lower(email) = lower('<email>');
```

Deletion requests come in as GitHub issues at https://github.com/kilmeh/contribute/issues.
Watch that tracker.

## Free tier notes

- Free projects are **paused after about a week without activity** (**verify**
  current policy). A paused project rejects inserts, so the site shows "We could not
  send your words". Restore it from the dashboard; sharing a link on social media
  after a quiet week needs a check first.
- Free tier storage (500 MB at the time of writing, **verify**) is far more than
  this needs.

## Security model and known limits

What protects the data:

- Row level security is on (and forced) for both tables. The only policies are
  `INSERT` for the `anon` role, with checks that mirror the table constraints.
- `anon` holds only column-level `INSERT` grants. All other privileges are revoked
  from `anon`, `authenticated` and `public`, including the ones Supabase grants by
  default. The client cannot set `created_at` or the entry `id`.
- Because `anon` has no `SELECT`, the API cannot return rows, and inserts must use
  `Prefer: return=minimal`. Upserts are impossible (they need `UPDATE`).
- Constraints: length limits on every text column, email format, allowed country
  codes (22 uppercase ISO codes or `other`; free text `country_other` required
  only for `other` and null otherwise),
  consent must be true, `credit_by_name` only with a name, deletion code format and
  uniqueness, one answer per (contributor, word), and an entry must reference an
  existing contributor.
- `dialect` is a stored generated column computed by `kilmeh_private.dialect_of(country)`.
  Nobody can insert or update it (not even the owner), so a contributor's country
  and dialect group can never disagree. The client never sends it, and `anon` has
  no grant on it. Both helper functions anon may execute (`text_ok`, `dialect_of`)
  are pure: they read no table. To change the mapping, change the function and
  `COUNTRY_DIALECT` in `js/logic.js` together (tests compare both with the agreed
  list).
- Roles: `anon` is the only role meant to insert. `authenticated` and `service_role`
  have no USAGE on the `kilmeh_private` schema, so the table CHECK constraints (which
  call `text_ok`) make their inserts fail. Read and delete as the dashboard owner
  (`postgres`), never through the API.
- One text rule, `kilmeh_private.text_ok`, applies to name, email, country_other,
  arabic, arabizi and both feminine fields, in the table CHECK and in the policy:
  at least one visible character (values made only of spaces, zero-width or bidi
  characters are rejected), no `=`, `+`, `-` or `@` as the first visible character,
  and no TAB, LF, VT, FF, CR, U+0085, U+2028 or U+2029 inside name, email and
  country_other. "Invisible" covers whitespace, zero-width, bidi and other format or
  filler characters (soft hyphen, U+034F, U+061C, Hangul and Braille fillers, variation
  selectors, the tag block); the exact list is in `schema.sql` and `INVISIBLE_RANGES`
  in `js/logic.js`, and a test keeps both identical. Nothing is stripped or
  rewritten, so ZWJ, ZWNJ, marks and bidi controls inside real Arabic text are kept
  exactly. The function lives in a schema the REST API does not expose.

Remaining limits (accepted for a first version):

- **No CAPTCHA and no server-side rate limit.** The anon key is public, so anyone
  can script inserts directly against the API and skip the page's checks (the
  honeypot field, the two-second minimum per word, client-side validation). The
  database constraints still apply to every row. Review data before publishing it.
- `word_id` is checked for format only, not against `words.json`.
- No script rule beyond the page's own check that the Arabic field contains Arabic
  letters and the Arabizi field contains none. Emoji, Cyrillic or other scripts in
  Arabizi are allowed on purpose (people write Arabizi in many ways), and the
  database does not check scripts at all. Review before publishing.
- The client generates the contributor id and deletion code. A script could reuse a
  known id to add entries to someone else's record only if it knew that random UUID.
- If abuse appears: add Cloudflare Turnstile with a Supabase Edge Function in front
  of the insert, or a Postgres trigger that rate-limits by time window.
- Personal data in the browser: until the contributor row is saved, the name and
  email are kept in `sessionStorage` of that tab (so a refresh does not lose them).
  They are removed as soon as the server accepts the contributor row (in test mode,
  after the simulated send; test mode never stores them in its log). Closing the
  tab clears it. Corrupt or tampered stored progress is discarded and the page
  starts fresh.
- Once the contributor row is saved, name, email, country and consent are locked
  for that browser session. A failed entries send is retried without resending the
  contributor. If the random deletion code ever collides with an existing one, the
  page makes a new code and contributor id and retries once.
- `frame-ancestors` cannot be set from a meta tag. If the host allows headers, add
  `Content-Security-Policy: frame-ancestors 'none'` there.
