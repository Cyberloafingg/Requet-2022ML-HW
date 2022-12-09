import pandas as pd
import random
import chunkdetection
import csv
import glob
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import scale

# dataset_list=['A', 'B1', 'B2', 'C', 'D']

ans = []
# for dataset in dataset_list:
dataset_folder = 'LabelDataSet/A0/'
files = glob.glob(dataset_folder + '*_label.csv')
# cnt=0
for i in range(1):
    file_name = files[i]
    print("Processing file: " + file_name)
    # if (i >= len_list[dataset]):
    # 	break
    file = pd.read_csv(file_name)  # wxh's csv name
    print(os.path.split(file_name)[1].split('/')[-1][:-17])
    feature_file = 'RequetDataSetNew/' +'A0'+'/PCAP_FILES/' + os.path.split(file_name)[1].split('/')[-1][:-17] + '.pcap'  # yhy's pcap name
    feature_class = chunkdetection.ChunkDetection(feature_file)
    len(feature_class.getFeature(1516209864093))
    lable_size = file.shape[0]
    for i in range(0, lable_size, 50):
        feature = feature_class.getFeature(file.iloc[i, 0])
        if not feature:
            continue
        feature.append(file_name + "-" + str(file.iloc[i, 0]))
        feature.extend(file.iloc[i, 1:])
        ans.append(feature)
out_file = open('test_data/test_data.csv', 'w', newline='')  # output   be careful of filename
writer = csv.writer(out_file)
keys = ['label' + str(i) for i in range(120)]
keys.extend(['filename_time', 'status', 'BuffWarning', 'Resolution'])
writer.writerow(keys)
for i in ans:
    writer.writerow(i)
out_file.close()
