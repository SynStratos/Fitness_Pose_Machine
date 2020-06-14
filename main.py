import time
import os

from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image
from utils.angles import preprocess_angles
from exercise import Exercise

if __name__ == "__main__":
    set_logger()
    #raise NotImplementedError

    ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
    global_config = os.path.join(os.getcwd(), "config/global_config.json")
    # TODO: get side
    exercise = Exercise(config=ex_config, side='s_w', fps=global_config['fps'])

    frames = []
    new_frame = True
    while(new_frame):
        _, processed_frame = process_image(new_frame) # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
        frames.append(processed_frame)

        if len(frames) >= 3:
            tic = time.clock()
            preprocessed_x = preprocess_angles(frames[-3:], mids=Exercise.mids)

            try:
                if exercise.process_frame(preprocessed_x[-2]):
                    #send message to client per ripetizione corretta
            except CompleteExerciseException:
                #aggiungi ripetizione corretta
                #send message to client per esercizio finito e interrompi invio
            except BadRepetitionException as bre:
                message = str(bre)
                #aggiungi ripetizione errata a client + messaggio su info errore
            except TimeoutError:
                #send message to client per esercizio finito per il timeout e interrompi invio
            finally:
                frames = frames[-2:]

            toc = time.clock()

            log.debug("time: %s" % str(toc-tic))

