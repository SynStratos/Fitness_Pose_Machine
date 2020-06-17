import time
import os
import json
from logger import set_logger, log
from exceptions import *
from pose_estimation import process_image
from utils.angles import preprocess_angles
from exercises.exercise import Exercise

if __name__ == "__main__":
    set_logger()
    #raise NotImplementedError

    ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
    global_config = os.path.join(os.getcwd(), "config/global_config.json")
    # TODO: get side
    with open(global_config) as f:
        global_config = json.load(f)
    exercise = Exercise(config=ex_config, side='s_w', fps=global_config['fps'])

    print(exercise.mids)


    #TODO: fix mids passati a preprocess angles perchè sono solo quelli degli angoli che mi interessano -> pick indici degli angoli sempre dal config e preprocess solo su quelli 
    #
    # frames = []
    # new_frame = True
    # while(new_frame):
    #     _, processed_frame = process_image(new_frame) # lo gestiamo separatamente all'arrivo di ogni frame senza il resto dello script? controllare i tempi di esecuzione
    #     frames.append(processed_frame)
    #
    #     if len(frames) >= 3:
    #         tic = time.clock()
    #         preprocessed_x = preprocess_angles(np.array(frames[-3:]), mids=exercise.mids)
    #         preprocessed_x = preprocess_angles(np.array(frames[-3: exercise.angles_index]), mids=exercise.mids)
    #         preprocessed_x = np.array(frames[-3:])
    #
    #         try:
    #             if exercise.process_frame(preprocessed_x[-2]):
    #                 #send message to client per ripetizione corretta
    #         except CompleteExerciseException:
    #             #aggiungi ripetizione corretta
    #             #send message to client per esercizio finito e interrompi invio
    #         except BadRepetitionException as bre:
    #             message = str(bre)
    #             #aggiungi ripetizione errata a client + messaggio su info errore
    #         except TimeoutError:
    #             #send message to client per esercizio finito per il timeout e interrompi invio
    #         finally:
    #             frames = frames[-2:]
    #
    #         toc = time.clock()
    #
    #         log.debug("time: %s" % str(toc-tic))
    #
