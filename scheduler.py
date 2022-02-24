import asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta
import utils


class Scheduler:
    """
    An object which uses the bot's asyncio event loop to execute tasks every minute, hour, month, or year

    If a daily, weekly, monthly, or yearly task has the value at_midnight set to True, the action will
    be performed at 9 am on the appropriate day
    """
    #  =============================================================== init

    def __init__(self, bot):
        self.bot = bot
        self._loop = bot.loop
        self._minutely = list()
        self._hourly = list()
        self._daily = list()
        self._weekly = list()
        self._monthly = list()
        self._yearly = list()

        # Actions that go off at midnight (default: 9 am)
        self._daily_midnight = list()
        self._weekly_midnight = list()
        self._monthly_midnight = list()
        self._yearly_midnight = list()

        self.reset_last_runs()

    def reset_last_runs(self):
        now = datetime.now()
        self._year_last_run = datetime(now.year, 1, 1)
        self._month_last_run = datetime(now.year, now.month, 1)
        self._day_last_run = datetime(now.year, now.month, now.day)
        self._hour_last_run = datetime(now.year, now.month, now.day, now.hour)
        self._loop.create_task(self._task_loop())

    # ===============================================================  Add Function To Task Group

    def add_minutely_task(self, task):
        self._minutely.append(task)

    def add_hourly_task(self, task):
        self._hourly.append(task)

    def add_daily_task(self, task, at_midnight=False):
        if at_midnight:
            self._daily_midnight.append(task)
        else:
            self._daily.append(task)

    def add_weekly_task(self, task, at_midnight=False):
        if at_midnight:
            self._weekly_midnight.append(task)
        else:
            self._weekly.append(task)

    def add_monthly_task(self, task, at_midnight=False):
        if at_midnight:
            self._monthly_midnight.append(task)
        else:
            self._monthly.append(task)

    def add_yearly_task(self, task, at_midnight=False):
        if at_midnight:
            self._yearly_midnight.append(task)
        else:
            self._yearly.append(task)

    # =============================================================== Execute Task Groups

    async def _run_minutely(self, currtime):
        try:
            print("Running minutely tasks...")
            for task in self._minutely:
                await task(currtime)
            print("Minutely tasks done.")
        except Exception as e:
            await utils.report(str(e), source="Failed to execute minutely task")

    async def _run_hourly(self, currtime):
        try:
            print("Running hourly tasks...")
            for task in self._hourly:
                await task(currtime)
            print("Hourly tasks done.")
        except Exception as e:
            await utils.report(str(e), source="Failed to execute hourly task")

    async def _run_daily(self, currtime, midnight=False):
        try:
            if midnight:
                print("Running daily (@midnight) tasks...")
                for task in self._daily_midnight:
                    await task(currtime)
            else:
                print("Running daily (@9am) tasks...")
                for task in self._daily:
                    await task(currtime)
            print("Daily tasks done.")
        except Exception as e:
            await utils.report(str(e), source="Failed to execute daily task")

    async def _run_weekly(self, currtime, midnight=False):
        try:
            if midnight:
                print("Running weekly (@midnight) tasks...")
                for task in self._weekly_midnight:
                    await task(currtime)
            else:
                print("Running weekly (@9am) tasks...")
                for task in self._weekly:
                    await task(currtime)
            print("Weekly tasks done.")
        except Exception as e:
            await utils.report(str(e), source="Failed to execute weekly task")

    async def _run_monthly(self, currtime, midnight=False):
        try:
            if midnight:
                print("Running monthly (@midnight) tasks...")
                for task in self._monthly_midnight:
                    await task(currtime)
            else:
                print("Running monthly (@9am) tasks...")
                for task in self._monthly:
                    await task(currtime)
            print("Monthly tasks done.")
        except Exception as e:
            await utils.report(str(e), source="Failed to execute monthly task")

    async def _run_yearly(self, currtime, midnight=False):
        try:
            if midnight:
                print("Running yearly (@midnight) tasks...")
                for task in self._yearly_midnight:
                    await task(currtime)
            else:
                print("Running yearly (@9am) tasks...")
                for task in self._yearly:
                    await task(currtime)
            print("Yearly tasks done.")
        except Exception as e:
            await utils.report(str(e), source="Failed to execute yearly task")

    # ===============================================================  Scheduler Loop

    """ 
    Executes every minute and runs the periodic tasks. 
    Checks if the hour, month, or year rolled over and, if so,
    executes the tasks scheduled on those time frames
    """
    async def _task_loop(self):
        try:
            while True:
                delta = 60 - datetime.now().second  # Calculate seconds until next minute
                await asyncio.sleep(delta)
                now = datetime.now()

                if now > self._year_last_run + relativedelta(years=1):
                    self._year_last_run = datetime(now.year, 1, 1)
                    self._loop.create_task(self._run_yearly(now))

                if now > self._month_last_run + relativedelta(months=1):
                    self._month_last_run = datetime(now.year, now.month, 1)
                    self._loop.create_task(self._run_monthly(now))

                if now > self._day_last_run + relativedelta(days=1):
                    self._day_last_run = datetime(now.year, now.month, now.day)
                    self._loop.create_task(self._run_daily(now, midnight=True))
                    if now.weekday() == 0:
                        self._loop.create_task(self._run_weekly(now, midnight=True))

                if now > self._hour_last_run + relativedelta(hours=1):
                    self._hour_last_run = datetime(now.year, now.month, now.day, now.hour)
                    self._loop.create_task(self._run_hourly(now))

                    # Run daily, weekly, monthly, and yearly tasks that are delayed until 9 am
                    if now.hour == 14:  # Bot runs in UTC, so make a +5 hour adjustment for EST
                        self._loop.create_task(self._run_daily(now))
                        if now.weekday() == 0:
                            self._loop.create_task(self._run_weekly(now))
                        if now.day == 1:
                            self._loop.create_task(self._run_monthly(now))
                            if now.month == 1:
                                self._loop(self._run_yearly(now))

                self._loop.create_task(self._run_minutely(now))

        except Exception as e:
            await utils.report(str(e), source="Failed to execute task loop")
