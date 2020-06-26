# import tornado / websocket
import tornado.ioloop
import tornado.web
import tornado.websocket

# import librerie di sistema
import json
import os
from termcolor import colored
from copy import copy
from datetime import datetime
import base64
import time

# import modello
import cv2
import numpy as np

# import custom
from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image, instantiate_model
from utils.angles import preprocess_angles

# improt exercises
from exercises.burpee import Burpee
from exercises.thruster import Thruster

# vars global
exercise = None  # esercizio specifico
joints_total = []
frames = []  # array che contiene i frames da elaborare
number_frames = 1  # contatore per mostrare frame elaborati
file_debug = None  # file di debugging
file_debug_dir = "debugging/"  # nome del file di debugging
flag_debug_csv = True
video_processing_dir = "video_processing/"  # directory where process videos arrived from client
width_resize_video = 240 #resizing video landscape -> ideal: 240
height_resize_video = 240 #resizing video portrait -> ideal: 240
fps = 10 # fps to elaborate video

# enum to set exercise
EXERCISE = {
    'burpee': Burpee,
    'thruster': Thruster
}

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    connections = set()

    # CORS allow all origin
    def check_origin(self, origin):
        return True

    def open(self):
        self.connections.add(self)
        self.set_nodelay(True)  # doc: non bufferizza
        print(colored('> Client connected', 'red'))

    def on_close(self):
        self.connections.remove(self)
        print(colored('> Client disconnected', 'red'))


    # this function is de facto: ingest_video()
    def on_message(self, message):
        global exercise
        global ex_config # loaded in main
        global global_config # loaded in main

        # read message arrived -> always in json format
        message_ = json.loads(message)

        # different messages IN <-> different computation
        # type of message:
        # "video_upload" -> incoming a video to process
        # "type_exercise" -> incoming a video to process

        # different messages OUT <-> different computation
        # type of message:
        # "console" -> message that client have to show in console.log
        # "video_processing_updates_title" -> update the client when processing the video -> changing the popup title
        # "video_processing_updates_text" -> update the client when processing the video -> changing the popup text
        # "video_processing_terminated" -> update the client that the processing is ended and send the results

        if message_['type'] == "video_upload":
            # message from the client (video) passed to function "ingest_video()"
            print(colored('> Video Upload File', 'red'))
            self.ingest_video(message_)

        elif message_['type'] == "type_exercise":
            # set right exercise
            print(colored('> Setting Exercise: ' + message_['exercise'], 'red'))
            exercise = EXERCISE[message_['exercise']](config=ex_config, side='s_e', fps=global_config['fps'])

        elif message_['type'] == "detection_initial_position":
            # detect initial position
            print(colored('> Message to detect initial position', 'red'))
            self.detect_initial_position(message_['data'])

    # this function ingest a single frame to detect the initial position
    # logic:
    # -arrive a frame
    # -pose detection
    # -if detects (all keyjoints && feet position) -> message ok
    # -if not detect (all keyjoints && feet position) -> message non_ok
    def detect_initial_position(self, frame):
        #frame = frame in base64
        #decode base64 -> ho l'immagine
        #posenet -> detect joings
        #check: all joints and feet
        pass

    # this function ingest video arrived from client
    def ingest_video(self, video):
        global video_processing_dir
        global width_resize_video
        global height_resize_video

        # useful to reset system
        global frames
        global exercise
        global joints_total
        global number_frames

        # useful for debugging
        global file_debug_dir
        global file_debug
        file_debug = file_debug_dir + str(datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".csv"

        # counters for repetitions
        reps_total = 0
        reps_ok = 0
        reps_wrong = 0

        # flag break
        flag_break = False

        print("Arrived a message of tipe: " + video['type'])
        print("Video extension: " + video['video_extension'])

        # TODO: valid only in case 1 client connected -> NO multi clients
        # prepare system for new ingest video -> erasing global vars -> not at the end of "ingest_video()" because if the clients disconnects, global vars never erased
        print(colored("> Erasing global variables", 'red'))
        [client.write_message({'type': 'console', 'text': "Erasing global variables on server"}) for client in
         self.connections]
        frames = []
        joints_total = []
        number_frames = 1

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
        [client.write_message({'type': 'video_processing_updates_title', 'update': 'Processing video...'}) for client in
         self.connections]
        # read first frame
        success, image = capture.read()

        # counter to update client
        count = 1
        while success:
            print(colored("> Processing frames: "+str(count), 'yellow'))
            [client.write_message(
                {'type': 'video_processing_updates_text', 'update': 'Processing frame: ' + str(count)}) for client in
             self.connections]
            [client.write_message({'type': 'console', 'text': 'Processing frame: ' + str(count)}) for client in
             self.connections]

            # get images resized
            image = cv2.resize(image, (w_video,
                                       h_video))  # tested -> saving the image is a frame of the video scaled at w_video, h_video -> cv2.imwrite("test.jpeg", image)

            # ingest image
            try:
                self.ingest_image(image)
            except GoodRepetitionException:
                # found a good repetition
                reps_total += 1
                reps_ok += 1
                print(colored("> Reps OK", 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition OK!'}) for client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Repetition OK!'}) for client in self.connections]
            except CompleteExerciseException:
                # exercise completed according to fixed reps
                print(colored("> Exercise ended. Fixed reps", 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise ended. Fixed reps'}) for client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Exercise ended. Fixed reps'}) for client in self.connections]
                flag_break = True
                break
            except NoneRepetitionException:
                # exercise timeout without repetitions
                print(colored("> Repetition time exceed", 'green'))
                [client.write_message({'type': 'console', 'text': 'Repetition time exceed'}) for client in self.connections]
            except BadRepetitionException as bre:
                # found wrong repetition + message
                reps_total += 1
                reps_wrong += 1
                message = str(bre)
                print(colored("> Reps BAD: " + message, 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition WRONG!: ' + message}) for client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Repetition WRONG!: ' + message}) for client in self.connections]
            except TimeoutError:
                # exercise in timeout
                print(colored("> Exercise Timeout", 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise Timeout'}) for client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Exercise Timeout'}) for client in self.connections]
                flag_break = True
                break

            count += 1
            # skip next frame according to fps
            capture.set(cv2.CAP_PROP_POS_MSEC, (count * 1000 / fps))
            success, image = capture.read()

        if not flag_break:
            # processing last repetition
            try:
                self.ingest_image(None, exercise_over=True)
            except GoodRepetitionException:
                # found a good repetition
                reps_total += 1
                reps_ok += 1
                print(colored("> Reps OK", 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition OK!'}) for client
                 in self.connections]
                [client.write_message({'type': 'console', 'text': 'Repetition OK!'}) for client in self.connections]
            except CompleteExerciseException:
                # exercise completed according to fixed reps
                print(colored("> Exercise ended. Fixed reps", 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise ended. Fixed reps'})
                 for client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Exercise ended. Fixed reps'}) for client in
                 self.connections]
            except NoneRepetitionException:
                # exercise timeout without repetitions
                print(colored("> Repetition time exceed", 'green'))
                [client.write_message({'type': 'console', 'text': 'Repetition time exceed'}) for client in
                 self.connections]
            except BadRepetitionException as bre:
                # found wrong repetition + message
                reps_total += 1
                reps_wrong += 1
                message = str(bre)
                print(colored("> Reps BAD: " + message, 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Repetition WRONG!: ' + message}) for
                 client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Repetition WRONG!: ' + message}) for client in self.connections]
            except TimeoutError:
                # exercise in timeout
                print(colored("> Exercise Timeout", 'green'))
                [client.write_message({'type': 'video_processing_updates_text', 'update': 'Exercise Timeout'}) for
                 client in self.connections]
                [client.write_message({'type': 'console', 'text': 'Exercise Timeout'}) for client in self.connections]


        # update client -> video terminated
        [client.write_message({'type': 'video_processing_terminated', 'reps_total': reps_total, 'reps_ok': reps_ok, 'reps_wrong': reps_wrong}) for client in self.connections]
        [client.write_message({'type': 'console', 'text': "Reps Total: " + str(reps_total) +"; Reps OK: " + str(reps_ok) +"; Reps WRONG: " + str(reps_wrong) +";"}) for client in self.connections]
        print(colored("Reps Total: " + str(reps_total) +"; Reps OK: " + str(reps_ok) +"; Reps WRONG: " + str(reps_wrong) +";", 'green'))

        # file not useful anymore -> removing
        print(colored("> Removing video file from server", 'red'))
        [client.write_message({'type': 'console', 'text': "Removing video file on server"}) for client in self.connections]
        capture.release()
        os.remove(file_name)


    # this function ingest single image and process the repetitions
    def ingest_image(self, image, exercise_over=False):
        global frames
        global exercise
        global joints_total
        global file_debug
        global flag_debug_csv

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
                # preprocessed_x = preprocess_angles(np.array(frames[-3:])[:, exercise.angles_index], mids=exercise.mids)
                preprocessed_x = preprocess_angles(np.array(frames[-3:]), indexes=exercise.angles_index, mids=exercise.medians)
                joints = joints_total[-2]

                # debugging: TODO remove in production
                if flag_debug_csv:
                    file = open(file_debug, "a+")
                    for element in preprocessed_x[1]:
                        file.write(str(element) + ",")
                    file.write("\n")
                    file.close()

                # for each exception -> throw -> will catch in "ingest_video()"
                try:
                    exercise.process_frame(preprocessed_x[-2], exercise_over,joints=joints)
                except GoodRepetitionException:
                    raise GoodRepetitionException
                except CompleteExerciseException:
                    raise CompleteExerciseException
                except NoneRepetitionException:
                    raise NoneRepetitionException
                except BadRepetitionException as bre:
                    message = str(bre)
                    raise BadRepetitionException(message)
                except TimeoutError:
                    raise TimeoutError
                finally:
                    frames = copy(frames[-2:])
                    joints_total = copy(joints_total[-2:])

        # stop signal -> process only last frames
        else:
            try:
                exercise.process_frame(None, exercise_over, joints=None)
            except GoodRepetitionException:
                raise GoodRepetitionException
            except CompleteExerciseException:
                raise CompleteExerciseException
            except NoneRepetitionException:
                raise NoneRepetitionException
            except BadRepetitionException as bre:
                message = str(bre)
                raise BadRepetitionException(message)
            except TimeoutError:
                raise TimeoutError


def make_app():
    return tornado.web.Application([
        (r"/thruster_video", WebSocketHandler)
    ], debug=True, websocket_ping_interval=0, websocket_max_message_size=1000000000)


if __name__ == "__main__":
    app = make_app()
    app.listen(5000)

    # create dir for debugging if not exists
    if not os.path.exists(file_debug_dir):
        os.makedirs(file_debug_dir)

    # instance once
    instantiate_model()
    set_logger()
    global_config = os.path.join(os.getcwd(), "config/global_config.json")  # per-exercise configuration
    ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")  # global configuration
    with open(global_config) as f:
        global_config = json.load(f)  # load JSON configuration

    # inference first image -> otherwise first frame processed slowly
    img_first = cv2.imread("first_frame_instance_model.jpg")
    process_image(img_first)


    # load the exercise
    # TODO: get side
    # TODO: elaborate first frame
    # exercise = Exercise(config=ex_config, side='s_e', fps=global_config['fps']) #TODO tirare fuori -> messaggio socket che sceglie esecizio (pagina client -> set_Exercise)
    # tornado.ioloop.IOLoop.instance().stop()
    tornado.ioloop.IOLoop.current().start()