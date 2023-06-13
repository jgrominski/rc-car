import asyncio
import base64
import json
import sys
from http.client import responses

import cv2 as cv
import numpy as np
import pygame
import websockets
from pygame.locals import *


async def main():
    uri = sys.argv[1]

    pygame.init()
    pygame.display.set_caption("RC Car Control App")

    screen = pygame.display.set_mode([1280, 720])

    lights_value = 0.0

    async with websockets.connect(uri) as websocket:
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == K_z:
                        if lights_value != 0.7:
                            lights_value = 0.7
                        else:
                            lights_value = 0.0
                    if event.key == K_x:
                        if lights_value != 1.0:
                            lights_value = 1.0
                        else:
                            lights_value = 0.7
                    if event.key == K_c:
                        if lights_value != 2.0:
                            lights_value = 2.0
                        else:
                            lights_value = 0.7

            drive_motor = 0.0
            turn_motor = 0.0

            keys = pygame.key.get_pressed()

            if keys[K_UP]:
                drive_motor += 1.0
            if keys[K_DOWN]:
                drive_motor -= 1.0
            if keys[K_RIGHT]:
                turn_motor += 1.0
            if keys[K_LEFT]:
                turn_motor -= 1.0

            output = json.dumps({
                "type": "CONTROL_MESSAGE",
                "data": {
                    "verticalSpeed": drive_motor,
                    "horizontalSpeed": turn_motor,
                    "lightsValue": lights_value
                }
            })

            await websocket.send(output)

            frame_json = json.loads(await websocket.recv())
            frame_b64 = np.frombuffer(base64.b64decode(
                frame_json["data"]["image"].encode('utf-8')), dtype=np.uint8)
            frame = cv.imdecode(frame_b64, cv.IMREAD_COLOR)

            frame = np.fliplr(frame)
            frame = np.rot90(frame)
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

            frame_to_surface = pygame.surfarray.make_surface(frame)
            screen.blit(frame_to_surface, (0, 0))
            pygame.display.flip()


if __name__ == "__main__":
    asyncio.run(main())
