import json
import os

import pandas as pd
import matplotlib.pyplot as plt

# config per ogni esercizio
ex_config = os.path.join(os.getcwd(), "config/thruster_config.json")
with open(ex_config) as f:
    ex_config = json.load(f)

# prelevo valori
mins = ex_config['mins']
maxs = ex_config['maxs']
mids = ex_config['mids']
tolerances = ex_config['tolerance']
angles_names = ex_config['angles_names']

nome_file = "debugging/29_06_2020_22_24_29.csv"

nome_file = nome_file[:-4]

data = pd.read_csv(nome_file + ".csv")
data = data.iloc[:, :-1].values

data_rep = pd.read_csv(nome_file + "_reps.csv", header=None)
data_rep = data_rep.iloc[:, :-1].values

# grafico comune
plt.plot(data[:, 0], label=angles_names[0], color='skyblue') # elbow
plt.plot(data[:, 1], label=angles_names[1], color='orange') #shoulder
#plt.plot(data[:, 2], label=angles_names[2], color='green') #hip
plt.plot(data[:, 2], label=angles_names[2], color='red') #knee

for el in data_rep:
    #print(el)
    color = "green"
    if el[1] == "ko":
        color = "red"
    elif el[1] == "timeout":
        color = "yellow"

    plt.axvline(x=el[0]-3, color = color)

plt.show()

for graph in range(len(mins)):
    plt.plot(data[:, graph], label=angles_names[graph], color='skyblue')
    plt.axhline(mins[graph], color='red')
    plt.fill_between(x=range(data.shape[0]), y1=maxs[graph] + tolerances[graph], y2=maxs[graph] - tolerances[graph])
    plt.axhline(mids[graph], color='orange')

    for el in data_rep:
        color = "green"
        if el[1] == "ko":
            color = "red"
        elif el[1] == "timeout":
            color = "yellow"

        plt.axvline(x=el[0] - 3, color=color)

    plt.show()
