# 0.4.0 (2024-11-08)

- Improve performance of `POST /api/repos/{repo_id}/logs` endpoint
- New environment variable `AUDITIZE_MONGODB_TLS` to support MongoDB TLS connections
- Add official support for Python 3.13
- Add official support for MongoDB 8
- Minor fixes and improvements
- **Breaking change**: Auditize now requires MongoDB to be configured with a Replica Set

# 0.3.0 (2024-10-24)

- Overhaul of the log filter UI
- Add favorite log filters feature
- The log search parameter selectors and the log table column selectors are now searchable
- Add an "About" entry in the user menu
- Display the last login date in the user management page
- Various minor UI improvements and bug fixes
- Upgrade backend dependencies

# 0.2.4 (2024-10-16)

- Disable Search indexing (Google, Bing, etc...) with noindex

# 0.2.3 (2024-10-11)

- New environment variable `AUDITIZE_COOKIE_SECURE` to set the `Secure` flag on the
  user session cookies (`false` by default)
- Minor improvements in the `auditize bootstrap-superadmin` command
- Minor UI bug fixes and improvements
- Rename the `AUDITIZE_BASE_URL` environment variable to `AUDITIZE_PUBLIC_URL`
- Remove the `auditize bootstrap-default-superadmin` command

# 0.2.2 (2024-10-07)

- Add a `AUDITIZE_CONFIG` environment variable to load the configuration from an environment file

# 0.2.1 (2024-10-04)

- First release on PyPI
- Add `auditize` script as a shortcut to `python -m auditize`
- Minor bug fixes and improvements in log UI
- Minor improvements in `python -m auditize` command

# 0.2.0 (2024-09-27)

- UI enhancements throughout the interface
- Complete redesign of the entity selector
- Backend and frontend dependencies update

# 0.1.0 (2024-09-04)

Initial Auditize release.
