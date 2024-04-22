import os
import dataclasses


@dataclasses.dataclass
class Config:
    base_url: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    _smtp_sender: str

    @classmethod
    def load_from_env(cls, env=None):
        if env is None:
            env = os.environ
        return cls(
            base_url=env.get("AUDITIZE_BASE_URL", "http://localhost:8000"),
            smtp_server=env.get("AUDITIZE_SMTP_SERVER"),
            smtp_port=int(env.get("AUDITIZE_SMTP_PORT", 0)),
            smtp_username=env.get("AUDITIZE_SMTP_USERNAME"),
            smtp_password=env.get("AUDITIZE_SMTP_PASSWORD"),
            _smtp_sender=env.get("AUDITIZE_SMTP_SENDER"),
        )

    @property
    def smtp_sender(self):
        return self._smtp_sender or self.smtp_username

    def is_smtp_enabled(self):
        return all((self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password))


config = Config.load_from_env()
