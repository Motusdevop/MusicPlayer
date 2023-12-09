import matplotlib.pyplot as plt

import json as js


with open("snippets.json") as f:
    dictory = js.load(f)

for key in dictory.keys():
    x = list(range(len(dictory[key])))
    y = dictory[key]
    print(x)
    print(y)
    fig, ax = plt.subplots()
    ax.plot(x, y)
    plt.show()
