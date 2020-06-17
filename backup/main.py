import json
import time
import os
import base64
from threading import Thread

from termcolor import colored
from datetime import datetime
import eventlet

eventlet.monkey_patch()

import cv2
import numpy
import numpy as np

from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image
from utils.angles import preprocess_angles
from exercise import Exercise

# socket
from io import BytesIO
from flask import Flask, copy_current_request_context
from flask_socketio import SocketIO, emit
import base64
from PIL import Image, ImageOps

# avvio flask + socketio
app = Flask(__name__)
app.config["SECRET_KEY"] = 'secret!'
socketio = SocketIO(app, always_connect=True, engineio_logger=True, cors_allowed_origins='*', async_mode='eventlet',
                    ping_timeout=10, ping_interval=2)

# vars globali
exercise = None
frames = []
number_frames = 0

# namespace
SOCKET_NAMESPACE = '/background_task'


# trigger del socket
@socketio.on('connect', namespace=SOCKET_NAMESPACE)
def connected():
    global exercise
    print(colored('Client connected', 'red'))

    # istanzio tutto ciò che serve una volta sola
    set_logger()
    ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
    global_config = os.path.join(os.getcwd(), "config/global_config.json")

    # TODO: get side
    with open(global_config) as f:
        global_config = json.load(f)

    exercise = Exercise(config=ex_config, side='s_w', fps=global_config['fps'])


@socketio.on('disconnect', namespace=SOCKET_NAMESPACE)
def disconnect():
    print(colored('Client disconnect', 'red'))


thread = None


@socketio.on('start-background', namespace=SOCKET_NAMESPACE)
def onDoSomething():
    print("entro in onDoSomething")
    global thread
    thread = socketio.start_background_task(background_thread)
    emit('message', 'checking is started', namespace=SOCKET_NAMESPACE)


def background_thread():
    print("thread partito")
    while True:
        print(colored("cia", 'yellow'))
        socketio.sleep(0.2)
        # socketio.emit('message', {'data': "ciao"}, namespace=SOCKET_NAMESPACE)


@socketio.on('test-async', namespace=SOCKET_NAMESPACE)
def test():
    print(colored("TEST_TEST_TEST", 'green'))


if __name__ == '__main__':
    socketio.run(app, debug=True)

# evento chiamato quando si fa l'upload di una immagine via client
# @socketio.on('image-client')
# def imageUpload(image):
#     # processing dell'immagine
#     print("Immagine arrivata dal client")
#
#     img = ImageOps.flip(Image.open(BytesIO(image)))
#     buffer = BytesIO()
#     img.save(buffer, format='Jpeg')
#
#     emit('image-server', buffer.getvalue())
#
# thread = None
#
#
# @socketio.on('start-background', namespace="/background")
# def onDoSomething():
#     print("entro in onDoSomething")
#     global thread
#     thread = socketio.start_background_task(background_thread)
#     emit('doingSomething', 'checking is started', namespace="/background")
#
#
# def background_thread():
#     print("thread partito")
#     emit('message', 'ciao', namespace="/background")
#
#
# @socketio.on('image-client')
# def ingestImage(imageDataUrl):
#     socketio.sleep(0)
#     global frames
#     global exercise
#     global number_frames
#
#     # aggiorno il client
#     number_frames += 1
#     emit('message', str(number_frames))
#     # socketio.emit("image-server-processed", number_frames)
#     print(colored("Frame elaborato: " + str(number_frames), 'yellow'))
#
#     # gestione frame: dataUrl -> to -> "new_frame"
#     new_frame = cv2.cvtColor(numpy.array(Image.open(BytesIO(imageDataUrl))), cv2.COLOR_RGB2BGR)
#
#     # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
#     _, processed_frame = process_image(new_frame)
#     frames.append(processed_frame)
#     print(processed_frame)
#
#     if len(frames) >= 3:
#         tic = time.clock()
#         preprocessed_x = preprocess_angles(np.array(frames[-3:])[:, exercise.angles_index], mids=exercise.mids)
#
#         try:
#             if exercise.process_frame(preprocessed_x[-2]):
#                 print(colored("Reps OK", 'green'))
#         # send message to client per ripetizione corretta
#         except CompleteExerciseException:
#             print(colored("Esercizio completato", 'red'))
#             # aggiungi ripetizione corretta
#             # send message to client per esercizio finito e interrompi invio
#
#         except BadRepetitionException as bre:
#             message = str(bre)
#             print(colored("Reps NO: " + message, 'red'))
#             # aggiungi ripetizione errata a client + messaggio su info errore
#         except TimeoutError:
#             print(colored("Timeout", 'red'))
#             # send message to client per esercizio finito per il timeout e interrompi invio
#
#         finally:
#             frames = frames[-2:]
#
#         toc = time.clock()
#
#         log.debug("time: %s" % str(toc - tic))
#
#
# if __name__ == '__main__':
#     socketio.run(app, debug=True)
#
# # if __name__ == "__main__":
# #     set_logger()
# #     # raise NotImplementedError
# #
# #     ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
# #     global_config = os.path.join(os.getcwd(), "config/global_config.json")
# #     # TODO: get side
# #     exercise = Exercise(config=ex_config, side='s_w', fps=global_config['fps'])
# #
# #     frames = []
# #     new_frame = True
# #     while (new_frame):
# #         # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
# #         _, processed_frame = process_image(new_frame)
# #         frames.append(processed_frame)
# #
# #         if len(frames) >= 3:
# #             tic = time.clock()
# #             preprocessed_x = preprocess_angles(frames[-3:], mids=Exercise.mids)
# #
# #             try:
# #                 if exercise.process_frame(preprocessed_x[-2]):
# #             # send message to client per ripetizione corretta
# #             except CompleteExerciseException:
# #             # aggiungi ripetizione corretta
# #             # send message to client per esercizio finito e interrompi invio
# #             except BadRepetitionException as bre:
# #                 message = str(bre)
# #                 # aggiungi ripetizione errata a client + messaggio su info errore
# #             except TimeoutError:
# #             # send message to client per esercizio finito per il timeout e interrompi invio
# #             finally:
# #                 frames = frames[-2:]
# #
# #             toc = time.clock()
# #
# #             log.debug("time: %s" % str(toc - tic))
