import typing
import asyncio
import asyncpraw
from collections import defaultdict

__version__ = "0.0.6"

EFunc = typing.Callable[[asyncpraw.models.Submission], typing.Any]

class EventClient(asyncpraw.Reddit):
    __slots__ = ("subscriptions", "event_loop")

    def __init__(self, *args, **kwargs):
        self.subscriptions: typing.Mapping[EFunc, typing.Mapping[str, set]] = defaultdict(lambda: {})
        self.event_loop = asyncio.get_event_loop()

        super().__init__(*args, **kwargs)

    def listen(self, *, subreddits: typing.List[str]):
        """
        A decorator to subscribe to events

        Keyword Args:
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
            try:
                for function in self.subscriptions.keys():
                    for subreddit, submission in self.subscriptions[function].items():
                        latest_submission = await self._fetch_data(subreddit)
                        if not submission:
                            self.subscriptions[function][subreddit] = latest_submission
                            continue
                        
                        if latest_submission.id != submission.id:
                            await function(latest_submission)

                        self.subscriptions[function][subreddit] = latest_submission

                        await asyncio.sleep(1)

            except RuntimeError:
                continue
            
    async def _fetch_data(self, subreddit: str) -> set:
        """
        Fetch the latest submissions of a subreddit

        Args:
            subreddit: The subreddit to fetch the submissions from
        
        Returns:
            A set of the most recent submissions
        """

        subreddit = await self.subreddit(subreddit)
        async for submission in subreddit.new(limit=1):
            return submission

    def subscribe(self, func: EFunc, subreddits: typing.List[str]) -> None:
        """
        Subscribe to a submission create event in the given subreddit

        Args:
            func: The function to call on a submission create event
            subreddits: The subreddits to listen for submissions
        
        Returns:
            None
        """

        for subreddit in subreddits:
            self.subscriptions[func].setdefault(subreddit, set())

    def unsubscribe(self, func, subreddits: typing.List[str]) -> None:
        """
        Unsubscribe from receiving submissions from the given subreddits

        Args:
            func: The function to remove the subscriptions from
            subreddits: The subreddits to unsubscribe from
        
        Returns:
            None

        Raises:
            KeyError if you didn't subscribe to the subreddit
        """

        for subreddit in subreddits:
            del self.subscriptions[func][subreddit]

    def run(self, *, run_forever=True) -> None:
        """
        Run the client and start listening to submissions

        Keyword Args:
            run_forever: Whether the event loop should run forever. This could be useful for discord bots.

        Returns:
            None
        """
        
        self.event_loop.create_task(self._get_submissions())
        if not self.event_loop.is_running() and run_forever:
            self.event_loop.run_forever()
    