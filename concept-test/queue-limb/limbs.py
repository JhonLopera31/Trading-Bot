from multiprocessing import Process, Queue
from random import Random, randint, choice
from time import sleep, time

FATAL_RESPONSE = 'fatal'
LOADING_RESPONSE = 'loading'
LIMB_ACTION = ['success', LOADING_RESPONSE, 'error', FATAL_RESPONSE]
BOT_ACTIONS = ['click', 'tap', 'move', 'press']


def doing():
    pass

def limb(input, output):
    print(f'Init limb [[{time()}]]')

    while True:
        request = input.get()
        bot = request['bot']
        print(f'Request {bot}: {request} [[{time()}]]')

        action = request["action"]
        if action == FATAL_RESPONSE:
            break

        delay = randint(1, 4)
        print(f'Doing {bot}: "{action}" | delay: {delay} [[{time()}]]')
        sleep(delay)

        response = {'bot': bot, 'action': action,
                    'response': choice(LIMB_ACTION)}
        output.put(response)

    print(f'Ending limb [[{time()}]]')


def bot(id, actions, output, input):
    sleep_time = Random(id)
    print(f'Init bot: {id} [[{time()}]]')

    while (actions > 0):
        sleep(sleep_time.randint(0, 1))
        action = {'bot': id, 'action': choice(BOT_ACTIONS)}
        output.put(action, block=False)

        result = input.get()
        print(f'Response {id}: {result} [[{time()}]]')
        if result['bot'] == id:
            if result['response'] == FATAL_RESPONSE:
                break

            if result['response'] == LOADING_RESPONSE:
                sleep(1)

        actions -= 1

    print(f'Ending bot: {id} [[{time()}]]')


def main():
    input_limb = Queue()
    output_limb = Queue()

    bots_processes = []
    print(f'Creating bot processes [[{time()}]]')
    for x in range(1, 4, 2):
        id_bot = randint(x*10, (x+1)*10)
        actions = randint(2, 8)
        process = Process(target=bot, args=(
            id_bot, actions, input_limb, output_limb,))
        bots_processes.append(process)
        process.start()

    print(f'Creating limb process [[{time()}]]')
    limb_process = Process(target=limb, args=(input_limb, output_limb,))
    limb_process.start()

    for process in bots_processes:
        process.join()

    input_limb.put({'bot': 'main', 'action': FATAL_RESPONSE})
    limb_process.join()
    print(f'Ending main [[{time()}]]')


if __name__ == '__main__':
    main()
