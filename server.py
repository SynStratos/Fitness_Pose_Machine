# import tornado / websocket
import os

from matplotlib.cm import get_cmap

try:
    # needed on windows
    os.system("for /f \"tokens=5\" %a in ('netstat -aon ^| find \"5000\" ^| find \"LISTENING\"') do taskkill /f /pid %a")
except:
    pass

import ssl
from abc import ABC
from io import BytesIO

import tornado.ioloop
import tornado.web
import tornado.websocket

# import librerie di sistema
import json
import os
from termcolor import colored
from copy import copy
import base64
import time
from PIL import Image
import cv2
import numpy as np
import datetime

# import custom
from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image, instantiate_model, cap_values, colors
from utils.angles import preprocess_angles
from utils.pose import get_orientation

# import exercises
from exercises.burpee import Burpee
from exercises.thruster import Thruster

##############
##############
##############

# CONFIGURATION

## available exercises dictionary
EXERCISE = {
    'burpee': Burpee,
    'thruster': Thruster
}

## load config file
server_config_file = os.path.join(os.getcwd(), "config/server_config.json")
with open(server_config_file) as f:
    config = json.load(f)

global_config_file = os.path.join(os.getcwd(), "config/global_config.json")
with open(global_config_file) as f:
    global_config = json.load(f)

video_processing_dir = config['video_processing_dir']
fps = config['fps']
height_resize_video = config['height']
width_resize_video = config['width']

# CSV DEBUGGING
flag_debug_csv = True
file_debug_dir = "debugging/"  # nome del file di debugging
file_debug = None  # file di debugging
file_debug_rep = None

# MODULE LEVEL PLACEHOLDERS
flag_check_initial_position = True
flag_check_process_exercise = True
orientation = None
exercise = None
frames = []
joints_total = []
exercise_name = None

# MODULE LEVEL COUNTERS
## current processed frame number
number_frames = 1
## counters for repetitions
reps_total = 0
reps_ok = 0
reps_wrong = 0
## last repetition exit
flag_break = False


####################################################################

def ingest_image(image, exercise_over=False):
    global frames
    global exercise
    global joints_total

    # if frame is a "real" image -> process
    if not exercise_over:
        # frame to process
        new_frame = image

        # process frame
        joints_person, processed_frame = process_image(new_frame, show_joints=False)
        joints_total.append(joints_person)
        frames.append(processed_frame)

        if flag_debug_csv:
            frame_x = copy(new_frame)
            cmap = get_cmap('hsv')
            for i, point in enumerate(joints_total[-1]):
                if all(point):  # is not (None, None):
                    rgba = np.array(cmap(1 - i / 18. - 1. / 36))
                    rgba[0:3] *= 255
                    # cv2.putText(canvas, str(i), org=point, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=colors[i])
                    cv2.circle(frame_x, point[0:2], 4, colors[i], thickness=-1)
            cv2.imwrite("images/" + str(number_frames) + "_" + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".jpg", frame_x)

        # execution on angles only if frames >=3 (outliers & interpolation)
        if len(frames) >= 3:
            preprocessed_x = preprocess_angles(np.array(frames[-3:]), indexes=exercise.angles_index, mids=exercise.medians, cap_values=cap_values)
            joints = joints_total[-2]
            # debugging: TODO remove in production -> flag_debug_csv = False
            # file_debug defined in -> ingest_video()
            if flag_debug_csv:
                with open(file_debug, "a+") as file:
                    for element in preprocessed_x[1, exercise.angles_index]:
                        file.write(str(element) + ",")
                    file.write("\n")

            try:
                # exceptions will be catched from super method calling this function
                exercise.process_frame(preprocessed_x[-2], exercise_over,joints=joints)
            finally:
                # remove unnecessary elements from angles and joints data structures
                frames = copy(list(preprocessed_x[-2:]))
                joints_total = copy(joints_total[-2:])

    # stop signal -> process only last frames
    else:
        # exceptions will be catched from super method calling this function
        exercise.process_frame(None, exercise_over, joints=None)


class WebSocketHandler(tornado.websocket.WebSocketHandler, ABC):
    connections = set()

    def check_origin(self, origin):
        # CORS allow all origin
        return True

    def open(self):
        # useful for debugging
        global file_debug_dir
        global file_debug
        global file_debug_rep
        global number_frames

        number_frames = 1
        self.connections.add(self)
        self.set_nodelay(True)  # doc: non bufferizza
        print(colored('> Client connected', 'red'))

        file_debug = file_debug_dir + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".csv"
        file_debug_rep = file_debug_dir + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + "_reps.csv"

    def on_close(self):
        global flag_check_initial_position
        global flag_check_process_exercise

        self.connections.remove(self)
        print(colored('> Client disconnected', 'red'))

        print(colored('> Resetting vars global', 'red'))

        flag_check_initial_position = True
        flag_check_process_exercise = True

    def on_message(self, message):
        """
        parse any message received from the client, identifies the type of method that will be run

        different messages IN <-> different computation
        type of message:
        "video_upload" -> incoming a video to process
        "type_exercise" -> incoming a video to process
        "detection_initial_position" -> incoming a frame to detect initial position
        "detection_webcam_exercise" -> incoming a frame to process the exercise
        "detection_webcam_exercise" -> user has stopped exercise

        different messages OUT <-> different computation
        type of message:
        "console" -> message that client have to show in console.log
        "video_processing_updates_title" -> update the client when processing the video -> changing the popup title
        "video_processing_updates_text" -> update the client when processing the video -> changing the popup text
        "stop_webcam_exercise" -> update the client that the processing is ended and send the results

        @param message: message received from the client
        @return:
        """
        global exercise_name, frames
        global flag_check_initial_position
        global flag_check_process_exercise

        # read message arrived -> always in json format
        message_ = json.loads(message)

        if message_['type'] == "video_upload":
            # message from the client (video) passed to function "ingest_video()"
            print(colored('> Video Upload File', 'red'))
            self.ingest_video(message_)

        elif message_['type'] == "type_exercise":
            # set right exercise
            print(colored('> Setting Exercise: ' + message_['exercise'], 'red'))
            # exercise = EXERCISE[message_['exercise']](config=None, side='s_e', fps=global_config['fps'])
            exercise_name = message_['exercise']

        elif message_['type'] == "detection_initial_position":
            # detect initial position
            print(colored('> Message to detect initial position', 'red'))
            self.__detect_initial_position__(message_['data'])

        elif message_['type'] == "detection_webcam_exercise":
            # manage the beginning of a webcam exercise
            print(colored('> Message to process exercise from webcam', 'red'))
            if not flag_break:
                self.__ingest_webcam_stream__(message_['data'])

        elif message_['type'] == "stop_initial_position":
            print(colored('> Message to stop detecting initial position from webcam', 'red'))
            # user sent a message to stop the process of the exercise
            # stop processing on-fly message from FE -> flag_check_initial_position = False
            flag_check_initial_position = False

        elif message_['type'] == "stop_webcam_process_exercise":
            print(colored('> Message to stop exercise processing from webcam', 'red'))
            # user sent a message to stop the process of the exercise
            # process last frames
            self.__ingest_webcam_stream__(message_['data'], last_one=True)
            # update client that server received this message
            [client.write_message(
                {'type': 'stop_webcam_process_exercise_executed', 'reps_total': reps_total, 'reps_ok': reps_ok,
                 'reps_wrong': reps_wrong}) for client in
                self.connections]
            # stop processing on-fly message from FE -> flag_check_process_exercise = False
            flag_check_process_exercise = False

        elif message_['type'] == "flag_check_initial_position":
            flag_check_initial_position = True
        elif message_['type'] == "flag_check_process_exercise":
            flag_check_process_exercise = True

    # -------------------------------------------------------------------------------------------------------- #

    def __clean_global_vars__(self):
        global orientation
        global exercise, frames, joints_total
        global flag_check_initial_position
        global flag_break
        global reps_ok, reps_wrong, reps_total, number_frames
        print(colored("> Erasing global variables", 'red'))
        [client.write_message({'type': 'console', 'text': "Erasing global variables on server"}) for client in
         self.connections]
        orientation = None
        frames = []
        flag_break = False
        joints_total = []
        number_frames = 1
        reps_ok = 0
        reps_wrong = 0
        reps_total = 0

    def __detect_initial_position__(self, image_data_url):
        """
        method that ingests a single frame from WEBCAM to detect the initial position
        manages exceptions related to missing joints of the body and feet position
        @param image_data_url: data url of the image to be decoded
        @return:
        """
        global orientation
        global exercise
        global flag_check_initial_position

        # TODO: ci penso se inserire il timeout dopo X tentativi
        #frame = frame in base64
        #decode base64 -> image
        frame = cv2.cvtColor(np.array(Image.open(BytesIO(base64.b64decode(image_data_url.split(",")[1])))), cv2.COLOR_RGB2BGR)

        if flag_check_initial_position:
            # resetting global variables
            self.__clean_global_vars__()
            # process image with pose estimation
            try:
                joints, _ = process_image(frame, accept_missing=False, no_features=True)
                orientation = get_orientation(joints[13], joints[10])

                print(colored("> Person detected correctly.", 'green'))
                [client.write_message({'type': 'initial_position_detected',
                                       'text': "Person detected correctly.",
                                       "orientation": "south-east" if orientation == "s_e" else "south-west"})
                 for client in self.connections]

                print(colored("> Setting flag_check_initial_position to False. Skipping other possible frames sent by FE.", 'green'))
                flag_check_initial_position = False

                # initialize exercise object once the position has been detected
                exercise = EXERCISE[exercise_name](config=None, side=orientation, fps=fps)

            except FeetException:
                print(colored("> Can't detect one or both foot.", 'red'))
                [client.write_message({'type': 'initial_position_error',
                                       'error': "Can't detect one or both foot."})
                 for client in self.connections]
            except NotFoundPersonException:
                print(colored("> Can't detect enough body joints.", 'red'))
                [client.write_message({'type': 'initial_position_error',
                                       'error': "Can't detect enough body joints. Try moving slowly."})
                 for client in self.connections]
            except Exception:
                pass
        else:
            print(colored("> Skipping frame to detect initial position.", 'green'))

    def __ingest_webcam_stream__(self, image_data_url, last_one=False):
        """

        @param last_one:
        @param image_data_url:
        @return:
        """
        global reps_total, reps_ok, reps_wrong

        global frames, joints_total, number_frames

        if not last_one:
            frame = cv2.cvtColor(np.array(Image.open(BytesIO(base64.b64decode(image_data_url.split(",")[1])))), cv2.COLOR_RGB2BGR)
        else:
            frame = None

        _ = self.__try_catch_images__(frame, webcam=True, last_one=last_one)
        number_frames += 1
        log.debug("Frame #", number_frames)

    def __try_catch_images__(self, image, webcam=False, last_one=False):
        """

        @param image:
        @param last_one: process last empty frame to check previous frame and stop execution - triggered at the end of a local video or by a 'stop' button from the the webcam interface
        @return:
        """
        global reps_total
        global reps_ok
        global reps_wrong
        global flag_check_process_exercise
        global flag_break

        if flag_check_process_exercise:
            # frame to process

            #flag used when this function is called by ingest_video()

            try:
                ingest_image(image, exercise_over=last_one)
            except GoodRepetitionException:
                # found a good repetition
                reps_total += 1
                reps_ok += 1
                if flag_debug_csv:
                    with open(file_debug_rep, "a+") as file:
                        file.write(str(number_frames) + ",ok,")
                        file.write("\n")

                print(colored("> Reps OK", 'green'))

                # message for offline video processing
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition OK!'}) for client in
                 self.connections]
                # message for online video processing (webcam)
                [client.write_message({'type': 'rep_ok'}) for client in
                 self.connections]
                # message offline + online
                [client.write_message({'type': 'console', 'text': 'Repetition OK!'}) for client in self.connections]

            except CompleteExerciseException as ex:
                # exercise completed and last repetition was good -> increase good rep counter and return exercise ended message
                if "last_good" in str(ex):
                    reps_total += 1
                    reps_ok += 1
                    print(colored("> Reps OK", 'green'))
                    # message for offline video processing
                    [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition OK!'}) for
                     client in
                     self.connections]
                    # message for online video processing (webcam)
                    [client.write_message({'type': 'rep_ok'}) for client in
                     self.connections]
                    # message offline + online
                    [client.write_message({'type': 'console', 'text': 'Repetition OK!'}) for client in self.connections]
                # exercise completed and last repetition was bad -> increase good rep counter and return exercise ended message + error log message
                else:
                    reps_total += 1
                    reps_wrong += 1
                    message = str(ex)
                    print(colored("> Reps BAD: " + message, 'green'))
                    # message for offline video processing
                    [client.write_message(
                        {'type': 'video_processing_updates_text', 'update': 'Repetition WRONG!: ' + message})
                     for client in self.connections]
                    # message for online video processing (webcam)
                    [client.write_message({'type': 'rep_wrong'}) for client in
                     self.connections]
                    # message offline + online
                    [client.write_message({'type': 'console', 'text': 'Repetition WRONG!: ' + message}) for client in
                     self.connections]
                # exercise completed according to fixed reps
                if webcam:
                    print(colored("> Exercise ended. Fixed number of repetitions reached", 'green'))
                    [client.write_message(
                        {'type': 'video_processing_terminated', 'reps_total': reps_total, 'reps_ok': reps_ok,
                         'reps_wrong': reps_wrong}) for client in self.connections]
                    [client.write_message({'type': 'console',
                                           'text': "Reps Total: " + str(reps_total) + "; Reps OK: " + str(
                                               reps_ok) + "; Reps WRONG: " + str(reps_wrong) + ";"}) for client in
                     self.connections]
                    print(colored(
                        "Reps Total: " + str(reps_total) + "; Reps OK: " + str(reps_ok) + "; Reps WRONG: " + str(
                            reps_wrong) + ";", 'green'))
                    flag_break = True

            except NoneRepetitionException:
                if not last_one:
                    # exercise timeout without repetitions
                    print(colored("> Too tight or none movement detected, try moving better", 'green'))
                    # message offline + online
                    [client.write_message({'type': 'console', 'text': 'Too tight or none movement detected, try moving better'}) for client in self.connections]
            except BadRepetitionException as bre:
                # found wrong repetition + message
                reps_total += 1
                reps_wrong += 1
                message = str(bre)
                if flag_debug_csv:
                    with open(file_debug_rep, "a+") as file:
                        file.write(str(number_frames) + ",ko,")
                        file.write("\n")
                print(colored("> Reps BAD: " + message, 'green'))
                # message for offline video processing
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition WRONG!: ' + message})
                 for client in self.connections]
                # message for online video processing (webcam)
                [client.write_message({'type': 'rep_wrong'}) for client in
                 self.connections]
                # message offline + online
                [client.write_message({'type': 'console', 'text': 'Repetition WRONG!: ' + message}) for client in
                 self.connections]
            except TimeoutError:
                # exercise in timeout (maximum number of waiting seconds for the whole exercise exceeded)
                if webcam:
                    if flag_debug_csv:
                        with open(file_debug_rep, "a+") as file:
                            file.write(str(number_frames) + ",timeout,")
                            file.write("\n")
                        print(colored("> Exercise Timeout", 'green'))

                    # stop processing on-fly messages from FE
                    flag_check_process_exercise = False

                    # message for offline video processing
                    [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise Timeout'}) for client in
                     self.connections]
                    # message for online video processing (webcam)
                    [client.write_message({'type': 'timeout_exercise'}) for client in
                     self.connections]
                    # message offline + online
                    [client.write_message({'type': 'console', 'text': 'Exercise Timeout'}) for client in self.connections]
                    # TODO: from client side, if webcam excercise, stream must be interrupted
                    flag_break = True

            return flag_break

        else:
            # on-fly frames from FE to skip
            print(colored("> Setting flag_check_initial_position to False. Skipping other possible frames sent by FE.",'green'))

    def ingest_video(self, video):
        """
        this function ingest video arrived from client
        """

        global orientation

        # useful to reset system
        global frames
        global exercise
        global joints_total
        global number_frames

        # reps counters and delimiter
        global reps_ok, reps_wrong, reps_total
        global flag_break

        # useful for debugging
        global file_debug_dir, file_debug, file_debug_rep

        # prepare system for new ingest video -> erasing global vars -> not at the end of "ingest_video()" because if the clients disconnects, global vars never erased
        # resetting global variables
        self.__clean_global_vars__()
        # print(colored("> Erasing global variables", 'red'))
        # [client.write_message({'type': 'console', 'text': "Erasing global variables on server"}) for client in
        #  self.connections]
        # #
        # orientation = None
        # frames = []
        # joints_total = []
        # number_frames = 1
        # #
        # reps_ok = 0
        # reps_wrong = 0
        # reps_total = 0
        # # flag break
        # flag_break = False

        # file debug save useful for save csv
        file_debug = file_debug_dir + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".csv"
        file_debug_rep = file_debug_dir + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + "_reps.csv"

        # saving file
        # update client
        [client.write_message({'type': 'video_processing_updates_title', 'update': 'Saving file to server...'}) for
         client in self.connections]
        file_name = video_processing_dir + time.strftime("%d_%m_%Y_%H_%M_%S") + "." + video['video_extension']
        file = open(file_name, "wb")
        file.write(base64.b64decode(video['data'].split(",")[1]))
        file.close()

        # opening file
        capture = cv2.VideoCapture(file_name)
        if not capture.isOpened():
            # update client
            [client.write_message({'type': 'error', 'text': 'Video file not valid'}) for client in self.connections]
            # file not useful anymore -> removing
            capture.release()
            os.remove(file_name)
            raise Exception("Could not open video device")

        # get width/height from video
        width = capture.get(3)
        height = capture.get(4)
        # portrait or landscape
        if width > height:
            # landscape -> fixed width, calculating height
            w_video = int(width_resize_video)
            h_video = int(w_video * height / width)
            print(colored("Landscape. w_video = " + str(w_video) + "; h_video = " + str(h_video), 'yellow'))
        else:
            # portrait -> fixed height, calculating width
            h_video = int(height_resize_video)
            w_video = int(h_video * width / height)
            print(colored("Portrait. w_video = " + str(w_video) + "; h_video = " + str(h_video), 'yellow'))

        # start processing video
        [client.write_message({'type': 'video_processing_updates_title', 'update': 'Detecting initial position...'})
         for client in self.connections]
        # read first frame
        success, image = capture.read()
        # process first frame to check initial position
        try:
            joints, _ = process_image(image, accept_missing=False, no_features=True)
            orientation = get_orientation(joints[13], joints[10])
            print(colored("> Person detected correctly: " + str(orientation), 'green'))
            [client.write_message({'type': 'initial_position_detected',
                                   'text': "Person detected correctly in video.",
                                   "orientation": "south-east" if orientation == "s_e" else "south-west"})
             for client in self.connections]

            # initialize exercise object once the position has been detected
            exercise = EXERCISE[exercise_name](config=None, side=orientation, fps=fps)
        except FeetException:
            print(colored("> Can't detect one or both foot.", 'red'))
            [client.write_message({'type': 'initial_position_error',
                                   'error': "Can't detect one or both foot."})
             for client in self.connections]
        except NotFoundPersonException:
            print(colored("> Can't detect enough body joints.", 'red'))
            [client.write_message({'type': 'initial_position_error',
                                   'error': "Can't detect enough body joints."})
             for client in self.connections]
        except Exception:
            print(colored("> Unexpected error.", 'red'))
            [client.write_message({'type': 'error',
                                   'text': "Unexpected error occured during video parsing."})
             for client in self.connections]

        # start processing video
        [client.write_message({'type': 'video_processing_updates_title', 'update': 'Processing video...'}) for
         client in
         self.connections]
        # counter to update client
        while success:
            print(colored("> Processing frames: "+str(number_frames), 'yellow'))
            [client.write_message({'type': 'update_number_frame', 'number': str(number_frames)}) for client in
             self.connections]
            [client.write_message({'type': 'console', 'text': 'Processing frame: ' + str(number_frames)}) for client in
             self.connections]

            # get images resized
            image = cv2.resize(image, (w_video, h_video))

            # ingest images
            flag_break = flag_break or self.__try_catch_images__(image)

            # stop processing for overall timeout or total number of repetitions reached
            if flag_break:
                break

            number_frames += 1
            # skip next frame according to fps
            capture.set(cv2.CAP_PROP_POS_MSEC, (number_frames * 1000 / fps))
            success, image = capture.read()

        if not flag_break:
            # processing last repetition
            _ = self.__try_catch_images__(image, last_one=True)

        # update client -> video terminated
        [client.write_message({'type': 'video_processing_terminated', 'reps_total': reps_total, 'reps_ok': reps_ok, 'reps_wrong': reps_wrong}) for client in self.connections]
        [client.write_message({'type': 'console', 'text': "Reps Total: " + str(reps_total) +"; Reps OK: " + str(reps_ok) +"; Reps WRONG: " + str(reps_wrong) +";"}) for client in self.connections]
        print(colored("Reps Total: " + str(reps_total) +"; Reps OK: " + str(reps_ok) +"; Reps WRONG: " + str(reps_wrong) +";", 'green'))

        # file not useful anymore -> removing
        print(colored("> Removing video file from server", 'red'))
        [client.write_message({'type': 'console', 'text': "Removing video file on server"}) for client in self.connections]
        capture.release()
        capture.release()
        os.remove(file_name)


def make_app():
    """
    instantiate torando web application
    @return: web app
    """
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(os.path.join("certificates", "server.crt"),
                            os.path.join("certificates", "server.key"))

    return tornado.web.Application([
        (r"/alke", WebSocketHandler)
    ], debug=True, websocket_ping_interval=0, websocket_max_message_size=1000000000, ssl_options=ssl_ctx)


if __name__ == "__main__":
    # set up session logger
    set_logger(level='debug')
    # set up web application
    app = make_app()

    app.listen(5000, ssl_options = {
        "certfile": os.path.join("certificates", "server.crt"),
        "keyfile": os.path.join("certificates", "server.key"),
    })



    # instantiate tf model before running the inference to prevent slow loading times
    instantiate_model()

    # inference first image -> otherwise first frame processed slowly
    img_first = cv2.imread("first_frame_instance_model.jpg")
    process_image(img_first)

    tornado.ioloop.IOLoop.current().start()
