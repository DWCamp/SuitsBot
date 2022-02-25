import redis
import utils


class StringCache:
    """
    StringCache is a bucket which supplies strings from a determined source.
    When the bucket begins running low, new values are fetched in the background.
    The task of fetching new values is defined by the `gather()` function, which
    has no default implementation and must be defined for every application of
    this class.

    NOTE: If the cache runs out, it will supply the only remaining value repeatedly
    until it can fill itself
    """

    CACHE_DELIMITER = "\n"
    DB_KEY_PREFIX = "STRING-CACHE-QUEUE-"

    def __init__(self, bot, cache_id, fill_size=10, fill_threshold=3, gather_limit=5):
        """
        Creates a StringCache, loads the saved queue from the database (if it exists)

        :param bot: The bot object (contains important properties like the async event loop)
        :param cache_id: The key for storing this queue in the database
            NOTE: If this key is not unique between caches, they will overwrite each other
            NOTE: This key is not used 'as is'. It is prepended with 'STRING-CACHE-QUEUE-' to
            help ensure no collisions with any existing database keys
        :param fill_size: The size the queue will be filled to (Default: 10)
            NOTE: depending on implementation of fill(), this value may be exceeded
        :param fill_threshold: The size limit that triggers a refill (Default: 3)
        :param gather_limit: The maximum number of gather() attempts to make while filling (Default: 5)
        """
        self.bot = bot
        self.cache_id = cache_id
        self.fill_size = fill_size
        self.fill_threshold = fill_threshold
        self.gather_limit = gather_limit

        self._locked = False
        self._loop = bot.loop
        self._redis_db = redis.StrictRedis(host='localhost', charset="utf-8", decode_responses=True)
        self._queue = []
        # Indicates that the last string has been returned and should be deleted when the cache refills
        self._stale = False

        # Load saved queue
        cached_list = self._redis_db.get(StringCache.DB_KEY_PREFIX + self.cache_id)
        if cached_list:
            self._queue = cached_list.split(StringCache.CACHE_DELIMITER)

    def __len__(self):
        return len(self._queue)

    def clear(self, refill=False):
        """
        Empties the cache.

        :param refill (bool) If "True", a refill will be triggered once the cache is empty
        """
        self._queue = []
        self._save()
        if refill:
            self.fill()

    def peek(self):
        """ Returns the next value in the cache without removing """
        if len(self._queue) == 0:
            return None
        return self._queue[0]

    def pop(self) -> str:
        """ Removes the next value in the cache and returns it. Returns 'None' if cache is empty """
        if len(self._queue) == 0:  # Return None if cache is empty
            value = None
        elif len(self._queue) == 1:  # If only one item left in cache, return it but do not remove it
            value = self._queue[0]
            self._stale = True  # Signal that the element in the queue should be purged upon refill
        else:  # Pop the next item off the queue and update the database
            value = self._queue.pop(0)
            self._save()

        # Fill cache if queue is running low
        if len(self) < self.fill_threshold:
            self.fill()
        return value

    def fill(self):
        """ A function which creates an async task to fill up the cache """
        self._loop.create_task(self._fill())

    async def gather(self) -> list:
        """
        This is the method which defines the logic by which new resources are acquired
        A typical use would be performing a JSON request to a web API. The result should
        be returned as a list
        :return: A list of items to store in the queue
        """
        raise NotImplementedError

    def _save(self) -> None:
        """ Save the current queue to the database """
        db_key = StringCache.DB_KEY_PREFIX + self.cache_id
        db_value = StringCache.CACHE_DELIMITER.join(self._queue)
        self._redis_db.set(db_key, db_value)

    async def _fill(self) -> None:
        """
        The asynchronous method which fills the queue using the `gather()` function.
        When called once, this function will lock itself until it finishes to prevent
        multiple concurrent activations. Any subsequent calls will instantly exit
        """
        try:
            if self._locked:
                print(f"Cache {self.cache_id} locked. Abandoning `_fill()`")
                return
            self._locked = True  # Lock fetching to prevent concurrent fetching
            print(f"Filling cache `{self.cache_id}`...")
            # Gather values
            gather_count = 0
            while len(self._queue) < self.fill_size and gather_count < self.gather_limit:
                gather_count += 1
                try:
                    values = await self.gather()
                    if self._stale and len(values) > 0:  # Remove stale entry when new values added
                        self._queue = []
                        self._stale = False  # Queue is no longer stale
                    self._queue.extend(values)
                except Exception as exc:
                    await utils.flag(alert=f"Failed fill attempt {gather_count} for StringCache `{self.cache_id}`",
                                     description=str(exc))

            # Send an error if failed to fill queue after reaching maximum attempts
            if len(self._queue) < self.fill_size:
                print("Exceeded gather attempts")
                await utils.report(f"Failed to fill ResourceCache `{self.cache_id}`\n"
                                   f"Attempts: {gather_count}\n"
                                   f"Queue size: {len(self._queue)}\n"
                                   f"Target: {self.fill_size}\n"
                                   f"Cache: `{', '.join(self._queue)}`")
            else:
                print(f"Cache `{self.cache_id}` filled!")
            self._locked = False
            self._save()
        except Exception as e:
            self._locked = True  # Don't lock up the queue
            await utils.report(f"Exception on `_fill()` for StringCache `{self.cache_id}` \n" + str(e))
