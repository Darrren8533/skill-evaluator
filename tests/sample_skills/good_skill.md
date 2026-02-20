# Database Migration Safety

## When to Use
Use this skill whenever you are:
- Writing a new database migration file
- Modifying an existing migration
- Running migrations in a staging or production environment
- Reviewing a PR that contains migration files

Do NOT use this skill for:
- Seeding development data
- Modifying application-level ORM models without schema changes

## Steps

1. **Check if the migration is reversible**
   - Every migration MUST have a `down()` method or equivalent rollback
   - If data will be deleted, add a backup step first

2. **Verify the migration is non-breaking**
   - Adding a nullable column: ✅ safe
   - Renaming a column without a transition period: ❌ breaking
   - Dropping a column still referenced in code: ❌ breaking

3. **Test locally before staging**
   ```bash
   npm run migrate:up
   # run your test suite
   npm run migrate:down
   npm run migrate:up
   ```

4. **Add a migration lock check**
   - Confirm no other migration is running (`SELECT * FROM schema_migrations WHERE is_running = true`)

5. **Document the migration**
   - Add a comment at the top of the file: what it does, why it was needed, estimated run time on production data size

## Example

**Bad migration (will cause downtime):**
```sql
ALTER TABLE users RENAME COLUMN email TO email_address;
```

**Good migration (zero-downtime rename):**
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN email_address VARCHAR(255);
-- Step 2: Backfill (in batches)
UPDATE users SET email_address = email WHERE email_address IS NULL;
-- Step 3: Add NOT NULL constraint after backfill
ALTER TABLE users ALTER COLUMN email_address SET NOT NULL;
-- Step 4: Drop old column in a separate migration after code is deployed
```

## Expected Output
- A migration file that can be safely applied and rolled back
- Zero application downtime during deployment
- A clear comment block explaining the migration intent
