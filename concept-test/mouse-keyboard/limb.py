from time import sleep
from multiprocessing import Pipe, Process
from math import ceil

from pyautogui import locateCenterOnScreen, click, write, hotkey, size


BREAK_VALUE = "3"
TIMEOUT = 0.5


class Action:

    DEFAULT_DELAY = 0.25

    class Step:
        CLICK_KIND = 'click'
        DOUBLE_CLICK_KIND = 'double_click'
        TYPING_KIND = 'typing'
        PRESS_KIND = 'press'

        Q1_REGION = 'q1'
        Q2_REGION = 'q2'
        Q3_REGION = 'q3'
        Q4_REGION = 'q4'

        TOP_REGION = 'top'
        BOTTOM_REGION = 'bottom'
        LEFT_REGION = 'left'
        RIGHT_REGION = 'right'

        def __init__(self, kind, delay, parameters):
            self.kind = kind
            self.delay = delay
            self.parameters = parameters

        def __repr__(self):
            return f'Kind: {self.kind} | Delay: {self.delay} | Params: {self.parameters}'

    def __init__(self):
        self.steps = []

    def click(self, pattern_path, region=None, delay=DEFAULT_DELAY):
        params = {'pattern': pattern_path, 'region': region}
        step = self.Step(self.Step.CLICK_KIND, delay, params)
        self.steps.append(step)

    def double_click(self, pattern_path, region=None, delay=DEFAULT_DELAY):
        params = {'pattern': pattern_path, 'region': region}
        step = self.Step(self.Step.DOUBLE_CLICK_KIND, delay, params)
        self.steps.append(step)

    def typing(self, text, delay=DEFAULT_DELAY):
        params = {'text': text}
        step = self.Step(self.Step.TYPING_KIND, delay, params)
        self.steps.append(step)

    def press(self, delay=DEFAULT_DELAY, *keys):
        params = {'keys': keys}
        step = self.Step(self.Step.PRESS_KIND, delay, params)
        self.steps.append(step)


def wait(func):
    def wrapper(self, step):
        sleep(step.delay)
        func(self, step)

    return wrapper


class HandlerUI:

    def __init__(self):
        def calculate_region():
            width, height = size()
            width -= 1  # index starts from zero not one.
            height -= 1
            half_width = ceil(width / 2)
            half_height = ceil(height / 2)

            return {Action.Step.Q1_REGION: (half_width, 0, width, half_height),
                    Action.Step.Q2_REGION: (0, 0, half_width, half_height),
                    Action.Step.Q3_REGION: (0, half_height, half_width, height),
                    Action.Step.Q4_REGION: (half_width, half_height, width, height),
                    Action.Step.TOP_REGION: (0, 0, width, half_height),
                    Action.Step.BOTTOM_REGION: (0, half_height, width, height),
                    Action.Step.LEFT_REGION: (0, 0, half_width, height),
                    Action.Step.RIGHT_REGION: (half_width, 0, width, height)}

        self.kinds = {Action.Step.CLICK_KIND: self._do_click,
                      Action.Step.DOUBLE_CLICK_KIND: self._do_double_click,
                      Action.Step.TYPING_KIND: self._do_typing,
                      Action.Step.PRESS_KIND: self._do_press}

        self.regions = calculate_region()
        self.locations = {}

    def do(self, action):
        for step in action.steps:
            sleep(step.delay)
            print(step)
            self.kinds[step.kind](step)
            print("")

    def _do_click(self, step):
        step.parameters['clicks'] = 1
        self.__click(step)

    # _do_click = wait(_do_click)

    def _do_double_click(self, step):
        step.parameters['clicks'] = 2
        self.__click(step)

    def _do_typing(self, step):
        params = step.parameters
        print(params)
        write(params['text'])

    def _do_press(self, step):
        params = step.parameters
        print(params)
        hotkey(*params['keys'])

    def __click(self, step):
        params = step.parameters
        print(f'p: {params}')

        # Minimal cache
        if not 'center' in params:
            region = params['region']

            if not region is None and not 'region_coordinates' in params:
                region_coordinates = self.regions[region]
                params['region_coordinates'] = region_coordinates

            region_coordinates = params['region_coordinates']
            cache_key = params['pattern'] + region
            center = self.locations.get(cache_key,
                                        locateCenterOnScreen(params['pattern'],
                                                             region=region_coordinates,
                                                             grayscale=True,
                                                             confidence=0.93))
            if center is None:
                raise ValueError(
                    f"Pattern is not in specified region. Region: '{region}' | Pattern: '{params['pattern']}'")

            params['center'] = center
            self.locations[cache_key] = center

        clicks = params['clicks']
        x, y = params['center']
        click(x, y, clicks=clicks)


class Limb:

    def __init__(self, pipe, handler_ui):
        self.pipe = pipe
        self.handler = handler_ui

    def do(self):
        print("Doing")
        count = 0
        while True:
            has_action = self.pipe.poll(TIMEOUT)
            if has_action:
                action = self.pipe.recv()
                print(f'{count}. Data: {action}')

                if action == BREAK_VALUE:
                    self.pipe.send(f'End connection {count}')
                    break

                try:
                    self.handler.do(action)
                except Exception as ex:
                    print(ex)
                    self.pipe.send(BREAK_VALUE)
                    break

                self.pipe.send(f'Action complete: {action}')

            count += 1
        print("end Doing")


def brain(limb_pipe):
    print("Thinking")

    sleep(5)

    open_olymptrade = Action()
    open_olymptrade.click('./patterns/url_input.png',
                          region=Action.Step.TOP_REGION)
    open_olymptrade.typing('https://olymptrade.com/platform', delay=0.1)
    open_olymptrade.press(0.1, 'enter')

    setup_env = Action()
    setup_env.click('./patterns/settings_button.png',
                    delay=10, region=Action.Step.Q2_REGION)
    setup_env.click('./patterns/charts_button.png',
                    delay=1, region=Action.Step.TOP_REGION)
    setup_env.click('./patterns/operations_button.png',
                    region=Action.Step.Q2_REGION)

    operation_up = Action()
    operation_up.click('./patterns/value_input.png',
                       delay=5, region=Action.Step.Q1_REGION)
    operation_up.press(0.1, 'ctrl', 'a')
    operation_up.typing('5')
    operation_up.click('./patterns/up_operation_button.png',
                       delay=1, region=Action.Step.Q1_REGION)
    operation_up.click('./patterns/value_input.png',
                       delay=2, region=Action.Step.Q1_REGION)
    operation_up.press(0.1, 'ctrl', 'a')
    operation_up.typing('1')

    operation_down = Action()
    operation_down.click('./patterns/value_input.png',
                         delay=5, region=Action.Step.Q4_REGION)
    operation_down.press(0.1, 'ctrl', 'a')
    operation_down.typing('10')
    operation_down.click('./patterns/down_operation_button.png',
                         delay=1, region=Action.Step.Q4_REGION)
    operation_down.click('./patterns/value_input.png',
                         delay=2, region=Action.Step.Q4_REGION)
    operation_down.press(0.1, 'ctrl', 'a')
    operation_down.typing('1')

    operations = [open_olymptrade, setup_env, operation_up, operation_down]

    for operation in operations:
        limb_pipe.send(operation)

        action = limb_pipe.recv()
        print(f'Response: {action}')

        if action == BREAK_VALUE:
            break 

    limb_pipe.send(BREAK_VALUE)

    print("end Thinking")


def limb(brain_pipe):
    handler = HandlerUI()
    limb = Limb(brain_pipe, handler)

    limb.do()


def main():

    limb_pipe, brain_pipe = Pipe()

    brain_process = Process(target=brain, args=(limb_pipe,))
    limb_process = Process(target=limb, args=(brain_pipe,))
    processes = [brain_process, limb_process]

    for process in processes:
        process.start()

    for process in processes:
        process.join()


if __name__ == '__main__':
    main()
