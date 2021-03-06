import json
import os

from termcolor import colored
import numpy as np
from copy import copy
import datetime

from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image, instantiate_model
from utils.angles import preprocess_angles
from utils.image import *

from exercises.thruster import Thruster

from exercises.burpee import Burpee

# CSV DEBUGGING
flag_debug_csv = True
file_debug_dir = "debugging/"  # nome del file di debugging
file_debug = None  # file di debugging

# vars globali
exercise = None
frames = []
joints_total = []
number_frames = 1
file = None


def ingest_image_local(image):
    """

    @param image:
    @return:
    """
    global frames
    global exercise
    global number_frames
    global file
    global joints_total

    # aggiorno il client
    print(colored("Frame processing: " + str(number_frames), 'yellow'))
    number_frames += 1

    new_frame = image

    # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
    joints_person, processed_frame = process_image(new_frame, show_joints=False)
    joints_total.append(joints_person)
    frames.append(processed_frame)

    if len(frames) >= 3:
        preprocessed_x = preprocess_angles(np.array(frames[-3:]), indexes=exercise.angles_index, mids=exercise.medians)
        print(preprocessed_x[1, exercise.angles_index])

        # debugging: TODO remove in production -> flag_debug_csv = False
        if flag_debug_csv:
            with open(file_debug, "a+") as file:
                for element in preprocessed_x[1, exercise.angles_index]:
                    file.write(str(element) + ",")
                file.write("\n")

        joints = joints_total[-2]

        try:
            exercise.process_frame(preprocessed_x[-2], joints=joints)
        except GoodRepetitionException:
            print(colored("Reps OK", 'green'))
            # send message to client per ripetizione corretta
        except CompleteExerciseException:
            print(colored("Esercizio completato: ripetizioni finite!", 'green'))
        except NoneRepetitionException:
            print(colored("Esercizio in timeout senza ripetizioni", 'red'))
        except BadRepetitionException as bre:
            message = str(bre)
            print(colored("Reps BAD: " + message, 'red'))
        except TimeoutError:
            print(colored("Timeout", 'red'))
        finally:
            frames = copy(frames[-2:])
            joints_total = copy(joints_total[-2:])


def ingest_video_local(exercise, path, number_of_frames, fps, w=None, h=None, rotation=0, show_joints=False):
    """

    @param exercise:
    @param path:
    @param number_of_frames:
    @param fps:
    @param w:
    @param h:
    @param rotation:
    @param show_joints:
    @return:
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
    global_config = os.path.join(os.getcwd(), "config/global_config.json")

    # load videos
    # file_name_debug = "burpee_2.mp4"
    # file_name_debug = "burpee_1.mp4"
    file_name_debug = "test.mp4"
    video_file = os.path.join(os.getcwd(), "test_videos/" + file_name_debug)

    # useful for debugging
    file_debug = file_debug_dir + file_name_debug.replace('.','') + "_" +str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".csv"

    # instance model
    instantiate_model()

    # TODO: get side
    with open(global_config) as f:
        global_config = json.load(f)

    # exercise = Burpee(config=None, side='s_e', fps=global_config['fps'])
    exercise = Thruster(config=None, side='s_e', fps=global_config['fps'])

    ingest_video_local(exercise, video_file, number_of_frames=80000, fps=global_config['fps'], h=global_config['height'])
