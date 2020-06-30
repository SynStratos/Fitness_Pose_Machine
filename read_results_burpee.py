import json
import os
import numpy as np

import pandas as pd
import matplotlib.pyplot as plt

# config per ogni esercizio
ex_config = os.path.join(os.getcwd(), "config/burpee_config.json")
with open(ex_config) as f:
    ex_config = json.load(f)

# prelevo valori
mins = ex_config['mins']
maxs = ex_config['maxs']
mids = ex_config['mids']
tolerances = ex_config['tolerance']
angles_names = ex_config['angles_names']


nome_file = "debugging/30_06_2020_00_08_04.csv"
nome_file = nome_file.split(".csv")[0]
data = pd.read_csv(nome_file + ".csv")
data = data.iloc[:, :-1].values

data_rep = pd.read_csv(nome_file + "_reps.csv", header=None)
data_rep = data_rep.iloc[:, :-1].values

# grafico comune

#plt.plot(data[:, 0], label=angles_names[0], color='skyblue')
#plt.plot(data[:, 1], label=angles_names[1], color='orange')
#plt.plot(data[:, 2], label=angles_names[2], color='green')
#plt.plot(data[:, 3], label=angles_names[3], color='red')
#plt.show()


for graph in range(1):
    #plt.plot(np.abs(np.abs(90-data[:, graph])-90), label=angles_names[graph], color='skyblue')
    #data_x = [d -90 if d > 90 else d for d in data[:, graph] ]
    #if data[:, graph] > 90:
    #    plt.plot(data[:, graph]-90, label=angles_names[graph], color='skyblue')
    #else:
    #    plt.plot(data[:, graph], label=angles_names[graph], color='skyblue')
    #plt.plot(data_x, label=angles_names[graph], color='skyblue')
    plt.plot(data[:, graph], label=angles_names[graph], color='black')
    plt.axhline(mins[graph], color='red')
    plt.fill_between(x=range(data.shape[0]), y1=maxs[graph] + tolerances[graph], y2=maxs[graph] - tolerances[graph])
    plt.axhline(mids[graph], color='orange')

    for el in data_rep:
        # print(el)
        color = "green"
        if el[1] == "ko":
            color = "red"
        elif el[1] == "timeout":
            color = "yellow"

        plt.axvline(x=el[0] - 4, color=color)

    plt.show()
