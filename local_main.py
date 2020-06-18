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
from utils.image import *
from exercises.exercise import Exercise


from copy import copy
from datetime import datetime


# vars globali
exercise = None
frames = []
number_frames = 1
file = None


def ingest_image_local(image):
    global frames
    global exercise
    global number_frames
    global file

    # aggiorno il client
    print(colored(len(frames), 'red'))
    print(colored("Frame processing: " + str(number_frames), 'yellow'))
    number_frames += 1

    new_frame = image

    # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
    _, processed_frame = process_image(new_frame)
    frames.append(processed_frame)

    if len(frames) >= 3:
        # tic = time.clock()
        preprocessed_x = preprocess_angles(np.array(frames[-3:])[:, exercise.angles_index], mids=exercise.mids)
        # debuggin

        for element in preprocessed_x[1]:
            file = open("debugging/debugging.csv", "a+")
            file.write(str(element) + ",")
            file.close()
        file = open("debugging/debugging.csv", "a+")
        file.write("\n")
        file.close()
        print(colored(preprocessed_x[1], 'green'))

        try:
            exercise.process_frame(preprocessed_x[-2])
        except GoodRepetitionException:
            print(colored("Reps OK", 'green'))
            # send message to client per ripetizione corretta
        except CompleteExerciseException:
            print(colored("Esercizio co mpletato", 'red'))
        except NoneRepetitionException:
            print(colored("Esercizio in timeout senza ripetizioni", 'red'))
        except BadRepetitionException as bre:
            message = str(bre)
            print(colored("Reps NO: " + message, 'red'))
        except TimeoutError:
            print(colored("Timeout", 'red'))
        finally:
            frames = copy(frames[-2:])


def ingest_video_local(exercise, path, number_of_frames, fps, w=None, h=None, rotation=0, show_joints=False):
    """
      method to ingest a video file
      path: path to the file
      fps: wanted frame per second
      method: function to apply to each frame
      w: width if resizing is needed
      h: height if resizing is needed
      rotation: degrees if rotation is needed
      """

    video = cv2.VideoCapture(path)

    width = video.get(3)
    height = video.get(4)

    landscape = width > height

    # by default i am expecting potrait videos
    if landscape:
        h, w = w, h
        # w, h = max(w, h), min(w, h)
    # else:
    # h, w = max(w, h), min(w, h)

    success, image = video.read()

    if not success:
        raise Exception("No frame in the video.")

    count = 0
    while success:
        if rotation > 0:
            image = rotate_image(image, rotation)

        image = image_resize(image, w, h)
        ingest_image_local(image)
        count += 1
        if count == number_of_frames:
            return
        video.set(cv2.CAP_PROP_POS_MSEC, (count * 1000 / fps))
        success, image = video.read()


if __name__ == '__main__':
    # istanzio tutto ciò che serve una volta sola
    set_logger()
    ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
    global_config = os.path.join(os.getcwd(), "config/global_config.json")

    video_file = os.path.join(os.getcwd(), "test_videos/thruster_1.mp4")

    # TODO: get side
    with open(global_config) as f:
        global_config = json.load(f)

    exercise = Exercise(config=ex_config, side='s_e', fps=global_config['fps'])

    ingest_video_local(exercise, video_file, number_of_frames=80, fps=global_config['fps'], h=180)
