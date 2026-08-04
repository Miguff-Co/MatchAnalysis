import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch, Sbopen
import pandas as pd


parser = Sbopen()
df, related, freeze, tactics = parser.event(69301)
print(df)
print(df.columns)