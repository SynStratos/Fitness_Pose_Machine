import json
import os

from termcolor import colored
import numpy as np
from copy import copy

from exercises.burpee import Burpee
from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image, instantiate_model
from utils.angles import preprocess_angles
from utils.image import *

from exercises.thruster import Thruster

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
    print(colored(len(frames), 'red'))
    print(colored("Frame processing: " + str(number_frames), 'yellow'))
    number_frames += 1

    new_frame = image

    # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
    joints_person, processed_frame = process_image(new_frame, show_joints=False)
    joints_total.append(joints_person)
    frames.append(processed_frame)

    if len(frames) >= 3:
        # tic = time.clock()
        # preprocessed_x = preprocess_angles(np.array(frames[-3:])[:, exercise.angles_index], mids=exercise.mids)
        preprocessed_x = preprocess_angles(np.array(frames[-3:]), indexes=exercise.angles_index, mids=exercise.mids)
        # debuggin

        # with open("debugging/debugging.csv", "w+") as file:
        #     for element in preprocessed_x[1]:
        #         file.write(str(element[:, exercise.angles_index]) + ",")
        #     file.write("\n")
        #
        # print(colored(preprocessed_x[1][:, exercise.angles_index], 'green'))

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
    # ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
    # ex_config = os.path.join(os.getcwd(), "config/burpee_config.json") #TODO: port to exercise class
    global_config = os.path.join(os.getcwd(), "config/global_config.json")

    video_file = os.path.join(os.getcwd(), "test_videos/burpee_1.mp4")
    # video_file = os.path.join(os.getcwd(), "test_videos/thruster_1.mp4")

    instantiate_model()

    # TODO: get side
    with open(global_config) as f:
        global_config = json.load(f)

    # exercise = Thruster(config=ex_config, side='s_e', fps=global_config['fps'])
    exercise = Burpee(config=None, side='s_e', fps=global_config['fps'])

    ingest_video_local(exercise, video_file, number_of_frames=80, fps=global_config['fps'], h=global_config['height'])
