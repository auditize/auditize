# Configuration

The base Auditize configuration is done through environment variables. The following variables are available:

| Variable | Required or default | Description |
|----------|-----------------------------|-------------|
| `AUDITIZE_BASE_URL` | **Required** | The base URL of your Auditize instance from which your users access Auditize. It will be used for instance to build the URL of the application in emails sent to users. |
| `AUDITIZE_JWT_SIGNING_KEY` | **Required** | The secret key used to sign the JWT tokens (user session cookies and access tokens). It must be a long random string. A [32 bytes long key is recommended](https://crypto.stackexchange.com/a/34866), you can generate one with the command `openssl rand -hex 32`. |
| `AUDITIZE_MONGODB_URI` | MongoDB instance running locally | The URI of the MongoDB instance used by Auditize. |
| `AUDITIZE_SMTP_SERVER` | | The SMTP server used to send emails. |
| `AUDITIZE_SMTP_PORT` |  | The SMTP server port. |
| `AUDITIZE_SMTP_USERNAME` |  | The SMTP account username. |
| `AUDITIZE_SMTP_PASSWORD` |  | The SMTP account password. |
| `AUDITIZE_SMTP_SENDER` | Defaults to `$AUDITIZE_SMTP_USERNAME` | The email address used to send emails. |
| `AUDITIZE_CORS_ALLOW_ORIGINS` | | A comma-separated list of origins allowed to make HTTP requests to Auditize. |
| `AUDITIZE_USER_SESSION_TOKEN_LIFETIME` | `43200` (12 hours) | The lifetime of the user session token in seconds. |
| `AUDITIZE_ACCESS_TOKEN_LIFETIME` | `600` (10 minutes) | The lifetime of the access token in seconds. |
| `AUDITIZE_ATTACHMENT_MAX_SIZE`| `5242880` (5MB) | The maximum size of a file attachment in bytes. |
| `AUDITIZE_CSV_MAX_ROWS` | `10000` | The maximum number of rows in a CSV export (`0` means no limit). |
