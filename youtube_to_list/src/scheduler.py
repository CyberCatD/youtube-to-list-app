import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.services import recipe_service

logger = logging.getLogger(__name__)

def purge_trash_job():
    """Scheduled job to purge trash every hour"""
    db: Session = SessionLocal()
    try:
        count = recipe_service.purge_trash(db)
        if count > 0:
            logger.info(f"Scheduled purge: Deleted {count} recipes from trash")
        else:
            logger.debug("Scheduled purge: Trash was empty")
    except Exception as e:
        logger.error(f"Error during scheduled trash purge: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler for periodic tasks"""
    scheduler = BackgroundScheduler()
    
    # Run every hour at the top of the hour (0 minutes)
    scheduler.add_job(
        purge_trash_job,
        trigger=CronTrigger(minute=0),  # Every hour at :00
        id='purge_trash',
        name='Purge trash folder',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Started background scheduler: Trash will be purged hourly")
    return scheduler
