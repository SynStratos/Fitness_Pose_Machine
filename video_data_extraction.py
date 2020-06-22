import os
import numpy as np
import cv2
import pandas as pd
from logger import set_logger
from pose_estimation import process_image, instantiate_model
from utils.image import rotate_image, image_resize
from utils.pose import get_orientation

################################################
# PARAMETERS TO EDIT TO RUN THE VIDEO PARSING #
################################################

video_directory = "./video_extraction_to_be_removed/video-dataset-burpee"
labels_file = "./video_extraction_to_be_removed/data-burpee.csv"
exercise_name = "burpee"
g_fps = 15
g_height = 240
g_width = None
################################################
######### DO NOT CHANGE ANYTHING BELOW ######### 
################################################


def _ingest_video(path, name, fps, method, df, w=None, h=None, rotation=0, show_joints=False):
    cat = df[df['filename'] == name]['target'].values[0]
    outputs = []
    joints = []
    video = cv2.VideoCapture(path)
    width = video.get(3)
    height = video.get(4)
    landscape = width > height
    # by default i am expecting potrait videos
    if landscape:
        h, w = w, h

    success, image = video.read()
    if not success:
        raise Exception("No frame in the video.")

    count = 0
    while success:
        if rotation > 0:
            image = rotate_image(image, rotation)
        image = image_resize(image, w, h)
        # for each frame collect the set of information (angles)
        j, o = method(image, show_joints=show_joints)
        joints.append(np.array(j))
        outputs.append(np.array(o))
        count += 1
        video.set(cv2.CAP_PROP_POS_MSEC, (count * 1000 / fps))
        success, image = video.read()

    joints = np.array(joints)
    outputs = np.array(outputs)
    orientation = get_orientation(joints[0][13], joints[0][10])

    return cat, joints, outputs, orientation


if __name__ == "__main__":
    set_logger(level='error')
    instantiate_model()
    # edit only if you want to skip a certain number of videos
    starting_index = 0
    # faileds = np.load("burpee_failed.npy", allow_pickle=True)
    labels_df = pd.read_csv(labels_file, sep=';')
    classifications = []
    all_joints = []
    all_outputs = []
    orientations = []
    failed = []
    successful = []
    video_files = [file_name for file_name in os.listdir(video_directory) if '.mp4' in file_name]
    for video_file in video_files[starting_index:]:
        g_video = os.path.join(video_directory, video_file)
        v_name = video_file.split('.')[0]
        # if v_name in faileds:
        print("Processing video: ", v_name)
        try:
            classification, g_joints, g_outputs, g_orientation = _ingest_video(g_video, name=v_name, fps=g_fps, method=process_image, df=labels_df, h=g_height, w=g_width)
            print('Ok')
            all_joints.append(g_joints)
            all_outputs.append(g_outputs)
            classifications.append(classification)
            orientations.append(g_orientation)
            successful.append(v_name)
        except Exception as e:
            print("Failed")
            print(str(e))
            failed.append(v_name)
        print("#------------------------------------#")

    np.save("{}_failed.npy".format(exercise_name), np.array(failed))
    np.save("{}_successful.npy".format(exercise_name), np.array(successful))
    np.save("{}_joints.npy".format(exercise_name), np.array(all_joints))
    np.save("{}_angles.npy".format(exercise_name), np.array(all_outputs))
    np.save("{}_classification.npy".format(exercise_name), np.array(classifications))
    np.save("{}_orientation.npy".format(exercise_name), np.array(orientations))
