#!/usr/bin/env python
# coding: utf-8

# In[12]:


import os
import time
import shutil

## Simulate Data ariving in the source folder


def Update():
    source_folder = [i for i in os.listdir("StreamData/Source") if i.endswith(".json")] + [i for i in os.listdir("StreamData/Archive") if i.endswith(".json")]
    exampledata_folder = [i for i in os.listdir("StreamData/ExampleData") if i.endswith(".json")]

    Difference = set(exampledata_folder).difference(set(source_folder))
    return Difference

Difference = Update()

while len(Difference) != 0:
    file = sorted(list(Difference), key = lambda x: int(x.split("_")[-1].split(".")[0]))[0]
    shutil.copyfile(f"StreamData/ExampleData/{file}", f"StreamData/Source/{file}")
    Difference = Update()
    time.sleep(0.5)
    if len(Difference) % 10 == 0:
        print(len(Difference))


# In[11]:


import os
import time
import shutil
### Reset Folders

def make_destination_empty(Path):
    files = os.listdir(Path)
    for file in files:
        try:
            shutil.rmtree(f"{Path}/{file}")
        except:
            os.remove(f"{Path}/{file}")

make_destination_empty("StreamData/Source")
make_destination_empty("StreamData/Target")
make_destination_empty("StreamData/CheckPoint")
make_destination_empty("StreamData/Archive")


# In[ ]:




