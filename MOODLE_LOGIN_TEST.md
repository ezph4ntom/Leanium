# Moodle login test (run after every build)

Five minutes after installing a new Leanium build, before relying on it. If any step fails, reinstall
the previous installer (your profile and passwords stay) and note what broke.

**Before installing:** export your passwords from the old build as a backup
(*Settings → Autofill and passwords → Password Manager → Settings → Export passwords → Download file*).
Keep the file somewhere private and delete old exports.

## 1. Save a login
- [ ] Open Moodle and sign out if you are signed in.
- [ ] Sign in with your username and password.
- [ ] Leanium asks **"Save password?"**. Click **Save**.
- [ ] Open *⋮ → Password Manager*: the Moodle login is in the list.

## 2. Autofill it
- [ ] Sign out of Moodle and reload the login page.
- [ ] Username and password fill in by themselves (or click the username field and pick the
      suggestion).
- [ ] Sign in works.

## 3. Export
- [ ] *Password Manager → Settings → Export passwords → Download file*.
- [ ] Windows asks where to save the `.csv` file; save it and check it opens.
- [ ] The file holds your passwords in plain text: move it somewhere private or delete it.

## 4. Quick look
- [ ] The window title and *Settings → About* say **Leanium** with the cup logo.
- [ ] Opening, switching and closing a few tabs works.

Write the date and build (for example `0.21.3.1-ui-tierB`) here when all boxes pass:

| Date | Build | Result |
| --- | --- | --- |
| | | |
