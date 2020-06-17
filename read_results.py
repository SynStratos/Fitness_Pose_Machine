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

data = pd.read_csv("debugging/debugging.csv")
data = data.iloc[:, :-1].values

for graph in range(len(mins)):
    plt.plot(data[:, graph], label='elbow', color='skyblue')
    plt.axhline(mins[graph], color='red')
    plt.axhline(maxs[graph] + tolerances[0], color='red')
    plt.axhline(maxs[graph] - tolerances[0], color='red')
    plt.axhline(mids[graph], color='orange')
    plt.show()




# multiple line plot
# plt.plot(data[:, 0], label='elbow', color='skyblue')
# plt.plot(data[:, 1], label='armpit', color='red')
# plt.plot(data[:, 2], label='hip', color='green')
# plt.plot(data[:, 3], label='knee', color='orange')
# plt.plot('x', 'y2', data=df, marker='', color='olive', linewidth=2)
# plt.plot('x', 'y3', data=df, marker='', color='olive', linewidth=2, linestyle='dashed', label="toto")
# plt.plot('x', 'y3', data=df, marker='', color='olive', linewidth=2, linestyle='dashed', label="toto")

