
import websockets
from server import client_handler
import asyncio


start_server = websockets.serve(client_handler,"localhost",8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()




