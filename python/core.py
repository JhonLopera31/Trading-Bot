import asyncio
from time import sleep
from math import ceil
from functools import partial
from multiprocessing import Pipe, Process

from websockets import serve
from pyautogui import locateCenterOnScreen, click, write, hotkey, size

BREAK_VALUE = "BREAK_PROCESS"
TIMEOUT = 0.5

class Action:

    DEFAULT_DELAY = 0.25

    class Region:
        Q1_REGION = 'q1'
        Q2_REGION = 'q2'
        Q3_REGION = 'q3'
        Q4_REGION = 'q4'

        TOP_REGION = 'top'
        BOTTOM_REGION = 'bottom'
        LEFT_REGION = 'left'
        RIGHT_REGION = 'right'

        @classmethod
        def calculate_regions(cls, size):
            width, height = size
            width -= 1  # index starts from zero not one.
            height -= 1
            half_width = ceil(width / 2)
            half_height = ceil(height / 2)

            return {cls.Q1_REGION: (half_width, 0, width, half_height),
                    cls.Q2_REGION: (0, 0, half_width, half_height),
                    cls.Q3_REGION: (0, half_height, half_width, height),
                    cls.Q4_REGION: (half_width, half_height, width, height),
                    cls.TOP_REGION: (0, 0, width, half_height),
                    cls.BOTTOM_REGION: (0, half_height, width, height),
                    cls.LEFT_REGION: (0, 0, half_width, height),
                    cls.RIGHT_REGION: (half_width, 0, width, height)}

    class Pattern:

        def __init__(self, path, grayscale=True, confidence=0.93):
            self.path = path
            self.grayscale = grayscale
            self.confidence = confidence

        def __repr__(self):
            return f'Path: {self.path} | Grayscale: {self.grayscale} | Confidence: {self.confidence}'

    class Step:
        CLICK_KIND = 'click'
        DOUBLE_CLICK_KIND = 'double_click'
        TYPING_KIND = 'typing'
        PRESS_KIND = 'press'

        def __init__(self, kind, delay, parameters):
            self.kind = kind
            self.delay = delay
            self.parameters = parameters

        def __repr__(self):
            return f'Kind: {self.kind} | Delay: {self.delay} | Params: {self.parameters}'

    def __init__(self):
        self.steps = []

    def click(self, pattern, region=None, delay=DEFAULT_DELAY):
        params = {'pattern': pattern, 'region': region}
        step = self.Step(self.Step.CLICK_KIND, delay, params)
        self.steps.append(step)

    def double_click(self, pattern, region=None, delay=DEFAULT_DELAY):
        params = {'pattern': pattern, 'region': region}
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


class HandlerUI:

    def __init__(self):
        self.kinds = {Action.Step.CLICK_KIND: self._do_click,
                      Action.Step.DOUBLE_CLICK_KIND: self._do_double_click,
                      Action.Step.TYPING_KIND: self._do_typing,
                      Action.Step.PRESS_KIND: self._do_press}

        self.regions = Action.Region.calculate_regions(size())
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

        # Minimal cache
        if not 'center' in params:
            region = params['region']
            pattern = params['pattern']

            region_coordinates = self.regions.get(region, None)
            cache_key = pattern.path + region
            center = self.locations.get(cache_key,
                                        locateCenterOnScreen(pattern.path,
                                                             region=region_coordinates,
                                                             grayscale=pattern.grayscale,
                                                             confidence=pattern.confidence))
            if center is None:
                raise ValueError(
                    f"Pattern is not in specified region. Region: '{region}':{region_coordinates} | Pattern: '{pattern}'")

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
        print("Doing...")
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
        print("End Doing")

class Bot:
    
    def __init__(self, pipe, limb):
        self.pipe = pipe
        self.limb = limb

    

