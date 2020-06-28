# import tornado / websocket
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
from pose_estimation import process_image, instantiate_model
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
##


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

        # execution on angles only if frames >=3 (outliers & interpolation)
        if len(frames) >= 3:
            preprocessed_x = preprocess_angles(np.array(frames[-3:]), indexes=exercise.angles_index, mids=exercise.medians)
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
        self.connections.add(self)
        self.set_nodelay(True)  # doc: non bufferizza
        print(colored('> Client connected', 'red'))

    def on_close(self):
        self.connections.remove(self)
        print(colored('> Client disconnected', 'red'))

    def on_message(self, message):
        """
        parse any message received from the client, identifies the type of method that will be run

        different messages IN <-> different computation
        type of message:
        "video_upload" -> incoming a video to process
        "type_exercise" -> incoming a video to process

        different messages OUT <-> different computation
        type of message:
        "console" -> message that client have to show in console.log
        "video_processing_updates_title" -> update the client when processing the video -> changing the popup title
        "video_processing_updates_text" -> update the client when processing the video -> changing the popup text
        "video_processing_terminated" -> update the client that the processing is ended and send the results

        @param message: message received from the client
        @return:
        """
        global exercise_name

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
            self.ingest_webcam_stream(message_['data'])

        elif message_['type'] == "stop_webcam_exercise":
            print(colored('> Message to stop exercise processing from webcam', 'red'))
            # manage a stop signal sent by the user (like a 'stop' button) to manually interrupt the exercise and check the previous frame
            self.ingest_webcam_stream(message_['data'], last_one=True)

            # TODO: invio messaggio di esercizio stoppato correttamente al fine del processing

    # -------------------------------------------------------------------------------------------------------- #

    def __detect_initial_position__(self, image_data_url):
        """
        method that ingests a single frame to detect the initial position
        @param image_data_url:
        @return:
        """
        global orientation
        global exercise
        # TODO: ci penso se inserire il timeout dopo X tentativi
        #frame = frame in base64
        #decode base64 -> image
        frame = cv2.cvtColor(np.array(Image.open(BytesIO(base64.b64decode(image_data_url.split(",")[1])))), cv2.COLOR_RGB2BGR)

        # process image with pose estimation
        try:
            joints, _ = process_image(frame, accept_missing=False, no_features=True)
            orientation = get_orientation(joints[13], joints[10])

            print(colored("> Person detected correctly.", 'green'))
            [client.write_message({'type': 'initial_position_detected',
                                   'text': "Person detected correctly.",
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
                                   'error': "Can't detect enough body joints. Try moving slowly."})
             for client in self.connections]
        except Exception:
            pass

    def ingest_webcam_stream(self, image_data_url, last_one=False):
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
        _ = self.__try_catch_images__(frame, last_one=last_one)

    def __try_catch_images__(self, image, last_one=False):
        """

        @param image:
        @param last_one: process last empty frame to check previous frame and stop execution - triggered at the end of a local video or by a 'stop' button from the the webcam interface
        @return:
        """
        global reps_total, reps_ok, reps_wrong
        # ingest image

        flag_break = False

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
            [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition OK!'}) for client in
             self.connections]
            [client.write_message({'type': 'console', 'text': 'Repetition OK!'}) for client in self.connections]
        except CompleteExerciseException:
            # exercise completed according to fixed reps

            print(colored("> Exercise ended. Fixed reps", 'green'))
            [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise ended. Fixed reps'}) for
             client in self.connections]
            [client.write_message({'type': 'console', 'text': 'Exercise ended. Fixed reps'}) for client in
             self.connections]
            # TODO: from client side, if webcam excercise, stream must be interrupted
            flag_break = True
        except NoneRepetitionException:
            if not last_one:
                # exercise timeout without repetitions
                print(colored("> Repetition time exceed", 'green'))
                [client.write_message({'type': 'console', 'text': 'Repetition time exceed'}) for client in self.connections]
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
            [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition WRONG!: ' + message})
             for client in self.connections]
            [client.write_message({'type': 'console', 'text': 'Repetition WRONG!: ' + message}) for client in
             self.connections]
        except TimeoutError:
            # exercise in timeout (maximum number of waiting seconds for the whole exercise exceeded)
            if flag_debug_csv:
                with open(file_debug_rep, "a+") as file:
                    file.write(str(number_frames) + ",timeout,")
                    file.write("\n")
            print(colored("> Exercise Timeout", 'green'))
            [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise Timeout'}) for client in
             self.connections]
            [client.write_message({'type': 'console', 'text': 'Exercise Timeout'}) for client in self.connections]
            # TODO: from client side, if webcam excercise, stream must be interrupted
            flag_break = True

        return flag_break

    # this function ingest video arrived from client
    def ingest_video(self, video):
        global orientation

        # useful to reset system
        global frames
        global exercise
        global joints_total
        global number_frames

        global reps_ok
        global reps_wrong
        global reps_total

        # useful for debugging
        global file_debug_dir
        global file_debug
        global file_debug_rep

        file_debug = file_debug_dir + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".csv"
        file_debug_rep = file_debug_dir + str(datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + "_reps.csv"

        # flag break
        flag_break = False

        # TODO: valid only in case 1 client connected -> NO multi clients
        # prepare system for new ingest video -> erasing global vars -> not at the end of "ingest_video()" because if the clients disconnects, global vars never erased
        print(colored("> Erasing global variables", 'red'))
        [client.write_message({'type': 'console', 'text': "Erasing global variables on server"}) for client in
         self.connections]
        frames = []
        joints_total = []
        number_frames = 1
        reps_ok = 0
        reps_wrong = 0
        reps_total = 0

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
            [client.write_message(
                {'type': 'video_processing_updates_text', 'update': 'Processing frame: ' + str(number_frames)}) for client in
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
    return tornado.web.Application([
        (r"/thruster_video", WebSocketHandler)
    ], debug=True, websocket_ping_interval=0, websocket_max_message_size=1000000000)


if __name__ == "__main__":
    # set up session logger
    set_logger()
    # set up web application
    app = make_app()
    app.listen(5000, ssl_options={
        "certfile": os.path.join("certificates", "server.crt"),
        "keyfile": os.path.join("certificates", "server.key"),
    })

    # instantiate tf model before running the inference to prevent slow loading times
    instantiate_model()

    # inference first image -> otherwise first frame processed slowly
    img_first = cv2.imread("first_frame_instance_model.jpg")
    process_image(img_first)

    tornado.ioloop.IOLoop.current().start()