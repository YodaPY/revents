import typing
import asyncio
import asyncpraw
import functools

EFunc = typing.Callable[[asyncpraw.models.Submission], typing.Any]

class EventClient(asyncpraw.Reddit):
    __slots__ = ("subscriptions", "event_loop")

    def __init__(self, *args, **kwargs):
        self.subscriptions: typing.Mapping[EFunc, typing.Mapping[str, set]] = {}
        self.event_loop = asyncio.get_event_loop()

        super().__init__(*args, **kwargs)

    def listen(self, *, subreddits: set):
        """
        A decorator to subscribe to events

        Args:
            subreddits: The subbreddits to listen for submissions
        """
        def decorator(func):
            self.subscribe(func, subreddits)

        return decorator

    async def _get_submissions(self) -> None:
        """
        Get all submissions for all subscribed subreddits
        """

        while True:
            for function in self.subscriptions.keys():
                for subreddit, submissions in self.subscriptions[function].items():
                    latest_submissions = await self._fetch_data(subreddit)
                    if not submissions:
                        self.subscriptions[function][subreddit] = latest_submissions
                        continue

                    new_submissions = latest_submissions - submissions
                    if new_submissions:
                        await function(list(new_submissions)[0])

                    self.subscriptions[function][subreddit] = latest_submissions

                    await asyncio.sleep(10)
            
    async def _fetch_data(self, subreddit: str) -> set:
        """
        Fetch the latest submissions of a subreddit

        Args:
            subreddit: The subreddit to fetch the submissions from
        
        Returns:
            A set of the most recent submissions
        """

        subreddit = await self.subreddit(subreddit)
        submissions = set()
        async for submission in subreddit.new(limit=10):
            submissions.add(submission)
        
        return submissions

    def subscribe(self, func: EFunc, subreddits: set) -> None:
        """
        Subscribe to a submission create event in the given subreddit

        Args:
            func: The function to call on a submission create event
            subreddits: The subreddits to listen for submissions
            sleep: The amount of time to sleep before fetching submissions of the subreddits
        
        Returns:
            None
        """

        self.subscriptions[func] = {
            subreddit: set()
            for subreddit in subreddits
        }

    def run(self) -> None:
        """
        Run the client and start listening to submissions
        """
        
        self.event_loop.create_task(self._get_submissions())
        self.event_loop.run_forever()
    