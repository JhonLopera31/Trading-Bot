import asyncio
from websockets import serve
from functools import partial
from multiprocessing import Pipe, Process

TIMEOUT = 0.5
BREAK_VALUE = "3"
SEND_VALUE = ["2", "4", "6"]

async def gateway_handler(pipe, websocket, path):
    print('Listening')
    
    while True:    

        data = None
        try:
            data = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT)
            pipe.send(data)
        except asyncio.TimeoutError:
            pass

        data = pipe.poll(TIMEOUT)
        if data:
            data = pipe.recv()
            await websocket.send(data)

            if "End connection" in data:
                break
    
    print(f'end Listening')
    asyncio.get_event_loop().stop()

def gateway(pipe):

    handler = partial(gateway_handler, pipe)
    start_server = serve(handler, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


def bot(pipe):
    print("Processing")
    count = 0
    while True:
        data = pipe.poll(TIMEOUT)
        if data:
            data = pipe.recv()
            print(f'{count}. Data: {data} | Type: {type(data)}')

            if data == BREAK_VALUE:
                pipe.send(f'End connection {count}')
                break

            if data in SEND_VALUE:
                pipe.send(f'Feedback, iter: {count}')

        count += 1
    print("end Processing")

def procurer():
    print("Start")
    gateway_pipe, bot_pipe = Pipe()

    gateway_process = Process(target=gateway, args=(gateway_pipe,))
    bot_process =  Process(target=bot, args=(bot_pipe,))
    processes = [gateway_process, bot_process]
    
    for process in processes:
        process.start()
    
    for process in processes:
        process.join()

    print("End")

if __name__ == "__main__":

    procurer()
