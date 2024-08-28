from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from auditize.config import get_config
from auditize.log.service import apply_log_retention_period


def build_scheduler():
    config = get_config()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        apply_log_retention_period,
        CronTrigger.from_crontab(config.log_expiration_schedule),
    )
    return scheduler
