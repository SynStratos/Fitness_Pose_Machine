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

# socket
from io import BytesIO
from flask import Flask, copy_current_request_context
from flask_socketio import SocketIO, emit

from PIL import Image, ImageOps
from copy import copy
from datetime import datetime

from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image
from utils.angles import preprocess_angles
from exercises.exercise import Exercise



# avvio flask + socketio
app = Flask(__name__)
app.config["SECRET_KEY"] = 'secret!'
socketio = SocketIO(app, always_connect=True, engineio_logger=True, cors_allowed_origins='*', async_mode='eventlet',
                    ping_timeout=7200, ping_interval=3600)

# vars globali
exercise = None
frames = []
joints_total = []
number_frames = 1
file = None
file_name = None


# trigger del socket
@socketio.on('connect')
def connected():
    global exercise
    global file_name

    print(colored('> Client conencted', 'red'))

    file_name = str(datetime.now())+".csv"

    # istanzio tutto ciò che serve una volta sola
    set_logger()
    ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
    global_config = os.path.join(os.getcwd(), "config/global_config.json")

    # TODO: get side
    with open(global_config) as f:
        global_config = json.load(f)

    exercise = Exercise(config=ex_config, side='s_e', fps=global_config['fps'])


@socketio.on('disconnect')
def disconnect():
    print(colored('> Client disconnected', 'red'))


@socketio.on('image-client')
def ingestImage(imageDataUrl):
    global frames
    global exercise
    global number_frames
    global file
    global joints_total

    # aggiorno il client
    print(colored(len(frames), 'red'))
    socketio.emit('frame-processing', str(number_frames))
    print(colored("Frame processing: " + str(number_frames), 'yellow'))
    number_frames += 1

    # gestione frame: dataUrl -> to -> "new_frame"
    new_frame = cv2.cvtColor(numpy.array(Image.open(BytesIO(imageDataUrl))), cv2.COLOR_RGB2BGR)

    # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
    joints_person, processed_frame = process_image(new_frame)
    joints_total.append(joints_person)
    frames.append(processed_frame)

    if len(frames) >= 3:
        # tic = time.clock()
        preprocessed_x = preprocess_angles(np.array(frames[-3:])[:, exercise.angles_index], mids=exercise.mids)
        # debuggin

        for element in preprocessed_x[1]:
            file = open("debugging/"+file_name, "a+")
            file.write(str(element) + ",")
            file.close()
        file = open("debugging/"+file_name, "a+")
        file.write("\n")
        file.close()
        print(colored(preprocessed_x, 'green'))

        joints = joints_total[-2]
        try:
            exercise.process_frame(preprocessed_x[-2], joints=joints)
        except GoodRepetitionException:
            print(colored("Reps OK", 'green'))
            # send message to client per ripetizione corretta
            socketio.emit('rep-ok')
        except CompleteExerciseException:
            print(colored("Esercizio completato", 'red'))
            # aggiungi ripetizione corretta
            # send message to client per esercizio finito e interrompi invio
            socketio.emit('message', 'Exercise Ended.')
        except NoneRepetitionException:
            print(colored("Esercizio in timeout senza ripetizioni", 'red'))
        except BadRepetitionException as bre:
            message = str(bre)
            print(colored("Reps NO: " + message, 'red'))
            # aggiungi ripetizione errata a client + messaggio su info errore
            socketio.emit('rep-no')

        except TimeoutError:
            print(colored("Timeout", 'red'))
            # send message to client per esercizio finito per il timeout e interrompi invio
            socketio.emit('message', 'Timeout Reached.')

        finally:
            frames = copy(frames[-2:])
            joints_total = copy(joints_total[-2:])


@socketio.on('video-ended')
def disconnect():
    print(colored('> Video ended', 'red'))


if __name__ == '__main__':
    socketio.run(app, debug=True)
