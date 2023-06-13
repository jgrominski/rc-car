import asyncio
import base64
import json
from time import time

import cv2 as cv
import websockets
from gpiozero import PWMLED, DistanceSensor, LightSensor, Motor


async def handler(websocket):
    print("\n-- Client connected --")

    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FPS, 30)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720)

    drive_motor = Motor(23, 24, 12)
    turn_motor = Motor(22, 27, 13)
    left_led = PWMLED(4)
    right_led = PWMLED(17)
    ldr = LightSensor(25)
    front_dist = DistanceSensor(echo=6, trigger=5)
    rear_dist = DistanceSensor(echo=26, trigger=16)

    right_led.off()
    left_led.off()

    rlight_value = 0.0
    llight_value = 0.0
    on_time = time()

    print("-- Started video stream --")

    async for msg in websocket:
        _, frame = cap.read()
        _, buffer = cv.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')

        frame_json = json.dumps({
            "type": "DISPLAY_MESSAGE",
            "data": {
                "image": jpg_as_text
            }
        })

        await websocket.send(frame_json)

        input = json.loads(msg)

        if (input["type"] == "CONTROL_MESSAGE"):
            drive_value = input["data"]["verticalSpeed"]
            turn_motor.value = input["data"]["horizontalSpeed"]

            if drive_value > 0.0 and front_dist.distance < 0.2:
                drive_value = 0.0
            if drive_value < 0.0 and rear_dist.distance < 0.2:
                drive_value = 0.0

            drive_motor.value = drive_value

            if input["data"]["lightsValue"] < 2.0:
                rlight_value = input["data"]["lightsValue"]
                llight_value = input["data"]["lightsValue"]
            elif ldr.value < 0.75 and time() - on_time > 2:
                llight_value = rlight_value = 0.7
                on_time = time()
            elif time() - on_time > 2:
                llight_value = rlight_value = 0.0
                on_time = time()

            if rlight_value > 0.0 and turn_motor.value > 0.0:
                rlight_value = 1.0
            if llight_value > 0.0 and turn_motor.value < 0.0:
                llight_value = 1.0

            if rlight_value != right_led.value:
                right_led.value = rlight_value
            if llight_value != left_led.value:
                left_led.value = llight_value

    drive_motor.close()
    turn_motor.close()
    right_led.close()
    left_led.close()
    ldr.close()
    front_dist.close()
    rear_dist.close()


async def main():
    print("~~~~~ RC Car Server started ~~~~~")
    async with websockets.serve(handler, "", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
