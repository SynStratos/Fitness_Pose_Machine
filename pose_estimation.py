import json
import os
import pylab as plt
import cv2
from matplotlib.pyplot import gcf
from matplotlib.cm import get_cmap
import numpy as np
import math
from scipy.ndimage import gaussian_filter

from logger import log
from models.tf2.keras_pose_estimation import get_model
from utils.pose import pad_right_down_corner
from utils.geometry import mid_joint, create_angle
from exceptions import *

# find connection in the specified sequence, center 29 is in the position 15
limbSeq = [[2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8], [2, 9], [9, 10], [10, 11], [2, 12], [12, 13], [13, 14],
           [2, 1], [1, 15], [15, 17], [1, 16], [16, 18], [3, 17], [6, 18]]

# the middle joints heatmap correpondence
mapIdx = [[31, 32], [39, 40], [33, 34], [35, 36], [41, 42], [43, 44], [19, 20], [21, 22], [23, 24], [25, 26], [27, 28],
          [29, 30], [47, 48], [49, 50], [53, 54], [51, 52], [55, 56], [37, 38], [45, 46]]

# joint colors
colors = [[255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0],
          [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255],
          [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]]

with open('./config/global_config.json') as f:
    g_config = json.load(f)

model_weights = os.path.join('./weights', g_config['model'])

model = None

with open('./config/pose_estimation_config.json') as f:
    pose_config = json.load(f)

boxsize = pose_config['boxsize']
scale_search = pose_config['scale_search']
stride, padValue = pose_config['stride'], pose_config['padValue']
thre1, thre2 = pose_config['thre1'], pose_config['thre2']


def instantiate_model():
    global model
    model = get_model(model_weights)


def _retrieve_model():
    return model


def _get_angles(joints):
    """
    method to calculate a set of specific angles starting from the joints extracted from the used pose estimation model
    @param joints: joints extracted from the pose estimation model
    @return: returns a set of angles calculated over the specified joints
    """
    angles = {
        "elbow_sx": (5, 6, 7),
        "elbow_dx": (2, 3, 4),
        "armpit_sx": (6, 5, 11),
        "armpit_dx": (3, 2, 8),
        "shoulder_sx": (0, 1, 5),
        "shoulder_dx": (0, 1, 2),
        "hip_sx": (5, 11, 12),
        "hip_dx": (2, 9, 10),
        "knee_sx": (11, 12, 13),
        "knee_dx": (8, 9, 10),
        "neck_front": ([11, 8], 1, 0),
        "foot_shoulder_sx": (13, 11, 5),
        "foot_shoulder_dx": (10, 8, 2),
        "hand_hip_knee_sx": (12, 11, 7),
        "hand_hip_knee_dx": (9, 8, 4),
        "hand_hip_foot_sx": (13, 11, 7),
        "hand_hip_foot_dx": (10, 8, 4),
        "head_hip_feet": (1, [11, 8], [10, 13]),  # unisco testa - centro dei fianchi e centro dei piedi
        "standing": (1, [10, 13], "axis_x")
        # TODO: add angle between hand-hip-foot -> useful for lateral sight e.g. burpees
    }

    ang = []
    for k, v in angles.items():
        try:
            v1 = mid_joint(v[0], joints)
            v2 = mid_joint(v[1], joints)
            if "axis" not in str(v[2]):
                v3 = mid_joint(v[2], joints)
            else:
                v3 = v[2]

            a_deg = create_angle(v1, v2, v3)
        except:
            a_deg = 0

        ang.append(a_deg)

    return ang


def visualize_person(canvas, person):
    """
    debugging method to plot the extracted joints on the image
    @param canvas:
    @param person:
    @return:
    """
    cmap = get_cmap('hsv')

    for i, point in enumerate(person):
        if all(point):  # is not (None, None):
            rgba = np.array(cmap(1 - i / 18. - 1. / 36))
            rgba[0:3] *= 255
            #cv2.putText(canvas, str(i), org=point, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=colors[i])
            cv2.circle(canvas, point[0:2], 4, colors[i], thickness=-1)
            to_plot = cv2.addWeighted(canvas, 0.3, canvas, 0.7, 0)
            plt.imshow(to_plot[:, :, [2, 1, 0]])
            fig = gcf()
            fig.set_size_inches(12, 12)
    plt.show()


def process_image(image, accept_missing=True, no_features=False, features_method=_get_angles, show_joints=False):

    """
    this method gets an image as input and returns the extracted joints and further features from it
    @param no_features: define if it is not needed to generate additional features but only person joints
    @param image: frame image
    @param features_method: method to extract needed features - _get_angles by default
    @param show_joints: print image with joints (debug)
    @param accept_missing: a not recognized person frame is accepted setting all joints to None and the process
        continues. A proper exception is raised if False.
    @return joints, features (angles)
    """
    #### sezione per indivudare i joint con il modello e mapparli - leave as it is
    multiplier = [x * boxsize / image.shape[0] for x in scale_search]
    heatmap_avg = np.zeros((image.shape[0], image.shape[1], 19))
    paf_avg = np.zeros((image.shape[0], image.shape[1], 38))

    for m in range(len(multiplier)):
        scale = multiplier[m]
        imageToTest = cv2.resize(image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        imageToTest_padded, pad = pad_right_down_corner(imageToTest, stride, padValue)

        input_img = np.transpose(np.float32(imageToTest_padded[:, :, :, np.newaxis]),
                                 (3, 0, 1, 2))  # required shape (1, width, height, channels)

        output_blobs = model.predict(input_img)

        # extract outputs, resize, and remove padding
        heatmap = np.squeeze(output_blobs[1])  # output 1 is heatmaps
        heatmap = cv2.resize(heatmap, (0, 0), fx=stride, fy=stride, interpolation=cv2.INTER_CUBIC)
        heatmap = heatmap[:imageToTest_padded.shape[0] - pad[2], :imageToTest_padded.shape[1] - pad[3], :]
        heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_CUBIC)

        paf = np.squeeze(output_blobs[0])  # output 0 is PAFs
        paf = cv2.resize(paf, (0, 0), fx=stride, fy=stride, interpolation=cv2.INTER_CUBIC)
        paf = paf[:imageToTest_padded.shape[0] - pad[2], :imageToTest_padded.shape[1] - pad[3], :]
        paf = cv2.resize(paf, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_CUBIC)

        heatmap_avg = heatmap_avg + heatmap / len(multiplier)
        paf_avg = paf_avg + paf / len(multiplier)

    #### qua trova tutti i joint presenti nell'immagine e li divide per parte del corpo -> all_peaks
    #### dove non sono stati individuati punti per quel determinato joint sarà presente comunque un array vuoto
    all_peaks = []
    peak_counter = 0

    for part in range(18):
        map_ori = heatmap_avg[:, :, part]
        map = gaussian_filter(map_ori, sigma=3)

        map_left = np.zeros(map.shape)
        map_left[1:, :] = map[:-1, :]
        map_right = np.zeros(map.shape)
        map_right[:-1, :] = map[1:, :]
        map_up = np.zeros(map.shape)
        map_up[:, 1:] = map[:, :-1]
        map_down = np.zeros(map.shape)
        map_down[:, :-1] = map[:, 1:]

        peaks_binary = np.logical_and.reduce(
            (map >= map_left, map >= map_right, map >= map_up, map >= map_down, map > thre1))
        peaks = list(zip(np.nonzero(peaks_binary)[1], np.nonzero(peaks_binary)[0]))  # note reverse
        peaks_with_score = [x + (map_ori[x[1], x[0]],) for x in peaks]
        id = range(peak_counter, peak_counter + len(peaks))
        peaks_with_score_and_id = [peaks_with_score[i] + (id[i],) for i in range(len(id))]

        all_peaks.append(peaks_with_score_and_id)
        peak_counter += len(peaks)

    ####
    connection_all = []
    special_k = []
    mid_num = 10

    for k in range(len(mapIdx)):
        score_mid = paf_avg[:, :, [x - 19 for x in mapIdx[k]]]
        candA = all_peaks[limbSeq[k][0] - 1]
        candB = all_peaks[limbSeq[k][1] - 1]
        nA = len(candA)
        nB = len(candB)
        indexA, indexB = limbSeq[k]
        if (nA != 0 and nB != 0):
            connection_candidate = []
            for i in range(nA):
                for j in range(nB):
                    vec = np.subtract(candB[j][:2], candA[i][:2])
                    norm = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
                    # failure case when 2 body parts overlaps
                    if norm == 0:
                        continue
                    vec = np.divide(vec, norm)

                    startend = list(zip(np.linspace(candA[i][0], candB[j][0], num=mid_num), np.linspace(candA[i][1], candB[j][1], num=mid_num)))

                    vec_x = np.array([score_mid[int(round(startend[I][1])), int(round(startend[I][0])), 0] \
                                      for I in range(len(startend))])
                    vec_y = np.array([score_mid[int(round(startend[I][1])), int(round(startend[I][0])), 1] \
                                      for I in range(len(startend))])

                    score_midpts = np.multiply(vec_x, vec[0]) + np.multiply(vec_y, vec[1])
                    score_with_dist_prior = sum(score_midpts) / len(score_midpts) + min(0.5 * image.shape[0] / norm - 1,
                                                                                        0)
                    criterion1 = len(np.nonzero(score_midpts > thre2)[0]) > 0.8 * len(score_midpts)
                    criterion2 = score_with_dist_prior > 0
                    if criterion1 and criterion2:
                        connection_candidate.append(
                            [i, j, score_with_dist_prior, score_with_dist_prior + candA[i][2] + candB[j][2]])

            connection_candidate = sorted(connection_candidate, key=lambda x: x[2], reverse=True)
            connection = np.zeros((0, 5))
            for c in range(len(connection_candidate)):
                i, j, s = connection_candidate[c][0:3]
                if (i not in connection[:, 3] and j not in connection[:, 4]):
                    connection = np.vstack([connection, [candA[i][3], candB[j][3], s, i, j]])
                    if (len(connection) >= min(nA, nB)):
                        break

            connection_all.append(connection)
        else:
            special_k.append(k)
            connection_all.append([])

    ####
    # last number in each row is the total parts number of that person
    # the second last number in each row is the score of the overall configuration
    subset = -1 * np.ones((0, 20))
    candidate = np.array([item for sublist in all_peaks for item in sublist])

    for k in range(len(mapIdx)):
        if k not in special_k:
            partAs = connection_all[k][:, 0]
            partBs = connection_all[k][:, 1]
            indexA, indexB = np.array(limbSeq[k]) - 1

            for i in range(len(connection_all[k])):  # = 1:size(temp,1)
                found = 0
                subset_idx = [-1, -1]
                for j in range(len(subset)):  # 1:size(subset,1):
                    if subset[j][indexA] == partAs[i] or subset[j][indexB] == partBs[i]:
                        subset_idx[found] = j
                        found += 1

                if found == 1:
                    j = subset_idx[0]
                    if (subset[j][indexB] != partBs[i]):
                        subset[j][indexB] = partBs[i]
                        subset[j][-1] += 1
                        subset[j][-2] += candidate[partBs[i].astype(int), 2] + connection_all[k][i][2]
                elif found == 2:  # if found 2 and disjoint, merge them
                    j1, j2 = subset_idx
                    log.debug("found = 2")
                    membership = ((subset[j1] >= 0).astype(int) + (subset[j2] >= 0).astype(int))[:-2]
                    if len(np.nonzero(membership == 2)[0]) == 0:  # merge
                        subset[j1][:-2] += (subset[j2][:-2] + 1)
                        subset[j1][-2:] += subset[j2][-2:]
                        subset[j1][-2] += connection_all[k][i][2]
                        subset = np.delete(subset, j2, 0)
                    else:  # as like found == 1
                        subset[j1][indexB] = partBs[i]
                        subset[j1][-1] += 1
                        subset[j1][-2] += candidate[partBs[i].astype(int), 2] + connection_all[k][i][2]

                # if find no partA in the subset, create a new subset
                elif not found and k < 17:
                    row = -1 * np.ones(20)
                    row[indexA] = partAs[i]
                    row[indexB] = partBs[i]
                    row[-1] = 2
                    row[-2] = sum(candidate[connection_all[k][i, :2].astype(int), 2]) + connection_all[k][i][2]
                    subset = np.vstack([subset, row])

    ####
    deleteIdx = [];
    for i in range(len(subset)):
        if subset[i][-1] < 4 or subset[i][-2] / subset[i][-1] < 0.4:
            deleteIdx.append(i)
    subset = np.delete(subset, deleteIdx, axis=0)
    ####
    persons = []
    for ss in subset:
        person = []
        for n, i in enumerate(ss[:-2]):
            if i == -1:
                person.append((None, None))
            for (a, b, _, d) in all_peaks[n]:
                if d == i:
                    person.append((a, b))
                    break
        persons.append(person)

    # TODO: define method to extract the single person if multiple
    try:
        person = persons[0]
    except:
        if accept_missing:
            log.warning("No person found in this frame: setting all joints to None.")
            person = [None]*19
        else:
            # may be useful for initial settings to check the joints of the person are visible
            raise NotFoundPersonException("Unable to find a person joints in the frame.")
    ####
    # joints = None
    if show_joints:
        visualize_person(image, person)
    if no_features:
        return person, None
    return person, features_method(person)
