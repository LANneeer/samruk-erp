import asyncio

loop: None | asyncio.AbstractEventLoop = None
def init_main_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

def await_sync(coroutine):
    return loop.run_until_complete(coroutine)