"""Scheduler service for automated weekly roulette execution."""

import asyncio
import threading

from typing import Dict, List

import schedule

from database.connection import get_database
from database.models import ChannelConfig
from .roulette import RouletteService


class SchedulerService:
    """Service for scheduling and running automated roulettes."""

    def __init__(self, roulette_service: RouletteService):
        """Initialize scheduler service."""
        self.roulette_service = roulette_service
        self.db = get_database()
        self._running = False
        self._thread: threading.Thread = None
        self._scheduled_jobs: Dict[str, object] = {}

    def _schedule_channel_roulette(self, config: ChannelConfig) -> None:
        """Schedule roulette for a specific channel configuration."""
        if not config.enabled:
            return

        # Create job function
        def run_channel_roulette():
            """Run roulette for this specific channel."""
            print(f"🎯 Running scheduled roulette for channel {config.channel_id}")
            try:
                # Run async roulette in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.roulette_service.send_roulette_message(
                        config.channel_id, test_mode=False
                    )
                )
                loop.close()

                if result["success"]:
                    print(
                        f"✅ Roulette completed for {config.channel_id}: {result['selected_member']['name']}"
                    )
                else:
                    print(
                        f"❌ Roulette failed for {config.channel_id}: {result['error']}"
                    )
            except Exception as e:
                print(f"💥 Error running roulette for {config.channel_id}: {e}")

        # Schedule the job
        job_key = f"{config.channel_id}_{config.day}_{config.time}"

        # Remove existing job if it exists
        if job_key in self._scheduled_jobs:
            schedule.cancel_job(self._scheduled_jobs[job_key])

        # Schedule new job
        job = (
            getattr(schedule.every(), config.day)
            .at(config.time)
            .do(run_channel_roulette)
        )
        self._scheduled_jobs[job_key] = job

        print(
            f"📅 Scheduled roulette for channel {config.channel_id}: {config.day} at {config.time}"
        )

    def update_schedules(self) -> None:
        """Update all schedules based on current database configuration."""
        print("🔄 Updating roulette schedules...")

        # Clear existing schedules
        schedule.clear()
        self._scheduled_jobs.clear()

        # Get all enabled configurations
        configs = self.db.get_all_enabled_configs()

        if not configs:
            print("ℹ️ No enabled roulette configurations found")
            return

        # Schedule each configuration
        for config in configs:
            self._schedule_channel_roulette(config)

        print(f"✅ Updated schedules for {len(configs)} channels")

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            print("⚠️ Scheduler is already running")
            return

        self._running = True
        self.update_schedules()

        def run_scheduler():
            """Run the scheduler loop."""
            print("🚀 Starting scheduler thread...")
            while self._running:
                schedule.run_pending()
                # Check every minute
                threading.Event().wait(60)
            print("🛑 Scheduler thread stopped")

        self._thread = threading.Thread(target=run_scheduler, daemon=True)
        self._thread.start()
        print("✅ Scheduler started successfully")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return

        print("🛑 Stopping scheduler...")
        self._running = False
        schedule.clear()
        self._scheduled_jobs.clear()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        print("✅ Scheduler stopped")

    def get_schedule_info(self) -> List[dict]:
        """Get information about all scheduled jobs."""
        jobs_info = []

        for job_key, job in self._scheduled_jobs.items():
            # Parse job key
            parts = job_key.split("_")
            if len(parts) >= 3:
                channel_id = "_".join(parts[:-2])  # Handle channel IDs with underscores
                day = parts[-2]
                time_str = parts[-1]

                jobs_info.append(
                    {
                        "channel_id": channel_id,
                        "day": day,
                        "time": time_str,
                        "next_run": job.next_run.isoformat() if job.next_run else None,
                        "job_key": job_key,
                    }
                )

        return jobs_info

    def force_update_schedules(self) -> None:
        """Force update schedules (useful when configuration changes)."""
        if self._running:
            self.update_schedules()
        else:
            print("⚠️ Scheduler is not running, schedules will be updated when started")
