#!/usr/bin/python3

# Copyright 2023 Philipp Andelfinger, Justin Kreikemeyer
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the “Software”), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#  
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#   
#   THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#   INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#   PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
#   ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import matplotlib.pyplot as plt
import pandas as pd

states = ["sus", "inf", "rec"]
data = pd.read_csv("reference.csv", header=None, names=states)
fig, ax = plt.subplots()
for s in states:
  data[s] = data[s].groupby(data[s].index // 100).sum()
  data[s].plot(ax=ax, label=s)
plt.legend()
plt.savefig("plot.pdf")
plt.show()
