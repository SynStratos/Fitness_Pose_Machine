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

data = pd.read_csv("debugging/debugging.csv")
data = data.iloc[:, :-1].values

# grafico comune

plt.plot(data[:, 0], label=angles_names[0], color='skyblue')
plt.plot(data[:, 1], label=angles_names[1], color='orange')
plt.plot(data[:, 2], label=angles_names[2], color='green')
plt.plot(data[:, 3], label=angles_names[3], color='red')
plt.show()


for graph in range(len(mins)):
    plt.plot(data[:, graph], label=angles_names[graph], color='skyblue')
    plt.axhline(mins[graph], color='red')
    plt.fill_between(x=range(data.shape[0]), y1=maxs[graph] + tolerances[graph], y2=maxs[graph] - tolerances[graph])
    plt.axhline(mids[graph], color='orange')
    plt.show()
