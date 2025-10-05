from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from auditize.config import get_config
from auditize.database.dbm import open_db_session
from auditize.log.service import LogService


async def log_expiration_job():
    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session)


def build_scheduler():
    config = get_config()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        log_expiration_job,
        CronTrigger.from_crontab(config.log_expiration_schedule),
    )
    return scheduler
