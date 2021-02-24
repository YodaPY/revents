Revents makes listening to events easier than ever, be it for discord bots or just simple testing.

**Currently revents only supports submission create events**

Install it with:
`pip install git+https://github.com/YodaPY/revents.git`

# Example Usage:
```py
from revents import EventClient

reddit_settings = {
    "client_id": "my client_id",
    "client_secret": "my_client_secret",
    "user_agent": "platform:app:version by /u/User"
}

client = EventClient(**reddit_settings)

@client.listen(subreddits={"Python"})
async def on_submission(submission):
    print(submission.title)

client.run()
```

# Performance boost
You can install [uvloop](https://github.com/MagicStack/uvloop) for a performance boost which will replace asyncio's default event loop.
```py
import uvloop

#your code

uvloop.install()
#run your client
```