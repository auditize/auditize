# Configuration

The base Auditize configuration is done through environment variables. The following variables are available:

| Variable | Required or default | Description |
|----------|-----------------------------|-------------|
| `AUDITIZE_CONFIG` | | The path to an environment file (key-value pairs) containing the configuration. If set, the configuration will be loaded from this file instead of environment variables. |
| `AUDITIZE_PUBLIC_URL` | **Required** | The public URL of your Auditize instance from which your users access Auditize. It will be used for instance to build the URL of the application in emails sent to users. |
| `AUDITIZE_JWT_SIGNING_KEY` | **Required** | The secret key used to sign the JWT tokens (user session cookies and access tokens). It must be a long random string. A [32 bytes long key is recommended](https://crypto.stackexchange.com/a/34866) (i.e 64 characters in hexadecimal representation), you can generate one with the command `openssl rand -hex 32`. |
| `AUDITIZE_MONGODB_URI` | MongoDB server running locally | The URI of the MongoDB server used by Auditize, it follows the [MongoDB URI format](https://docs.mongodb.com/manual/reference/connection-string/), example: `mongodb://user:password@localhost:27017/`. |
| `AUDITIZE_MONGODB_TLS` | `false` | Whether the MongoDB connection should use TLS (it must be set to `true` for MongoDB Atlas). |
| `AUDITIZE_DB_NAME` | `auditize` | The main database name. |
| `AUDITIZE_SMTP_SERVER` | | The SMTP server used to send emails. |
| `AUDITIZE_SMTP_PORT` |  | The SMTP server port. |
| `AUDITIZE_SMTP_USERNAME` |  | The SMTP account username. |
| `AUDITIZE_SMTP_PASSWORD` |  | The SMTP account password. |
| `AUDITIZE_SMTP_SENDER` | Defaults to `$AUDITIZE_SMTP_USERNAME` | The email address used to send emails. |
| `AUDITIZE_LOG_EXPIRATION_SCHEDULE` | `0 1 * * *` (every day at 1AM) | The schedule at which expired logs are deleted. |
| `AUDITIZE_COOKIE_SECURE` | `false` | Whether the user session cookie should be [secure](https://en.wikipedia.org/wiki/Secure_cookie) (only sent over HTTPS). It is recommended to set this to `true` in production. |
| `AUDITIZE_CORS_ALLOW_ORIGINS` | | A comma-separated list of origins allowed to make HTTP requests to Auditize. |
| `AUDITIZE_USER_SESSION_TOKEN_LIFETIME` | `43200` (12 hours) | The lifetime of user session tokens in seconds. |
| `AUDITIZE_ACCESS_TOKEN_LIFETIME` | `600` (10 minutes) | The lifetime of access tokens in seconds. |
| `AUDITIZE_ATTACHMENT_MAX_SIZE`| `5242880` (5MB) | The maximum file size of attachments in bytes. |
| `AUDITIZE_CSV_MAX_ROWS` | `10000` | The maximum number of rows in CSV exports (`0` means no limit). |
