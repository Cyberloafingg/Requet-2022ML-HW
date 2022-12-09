import warnings
import numpy as np

warnings.filterwarnings("ignore")
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

Tree_num = 200
train_file_nameA0 = 'TrainData/train_A0_resolution.csv'
train_file_nameA1 = 'TrainData/train_A1_resolution.csv'
train_file_nameA2 = 'TrainData/train_A2_resolution.csv'
train_file_nameA3 = 'TrainData/train_A3_resolution.csv'

A0 = pd.read_csv(train_file_nameA0)
A1 = pd.read_csv(train_file_nameA1)
A2 = pd.read_csv(train_file_nameA2)
A3 = pd.read_csv(train_file_nameA3)
Dataset_List = [A0, A1, A2, A3]
name_list = ["Status", "BuffWarning", "Resolution"]
acc_all = []
for i in range(4):
    acc_item = []
    for j in range(-1, 0):
        train_data = Dataset_List[i].append(Dataset_List[(i + 1) % 4]).append(Dataset_List[(i + 2) % 4])
        test_data = Dataset_List[(i + 3) % 4]

        x_train = pd.concat([train_data.iloc[:, :-10], train_data.iloc[:, 125:127]], axis=1)
        y_train = train_data.iloc[:, j]

        x_test = pd.concat([test_data.iloc[:, :-10], test_data.iloc[:, 125:127]], axis=1)
        y_test = test_data.iloc[:, j]
        RF = RandomForestClassifier(n_estimators=Tree_num, criterion="entropy")
        RF.fit(x_train, y_train)
        y_pred = RF.predict(x_test)
        accuracy = accuracy_score(y_pred, y_test)
        print(
            f'A{i}, A{(i + 1) % 4}, A{(i + 2) % 4} as train data, A{(i + 3) % 4} as test data, label = {name_list[j]}, accuracy = {accuracy}')
        acc_item.append(accuracy)
    acc_all.append(acc_item)
acc_mat = np.array(acc_all)
print(f'{np.average(acc_mat, axis=0)}')