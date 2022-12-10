import pandas as pd
import joblib
from sklearn.metrics import accuracy_score,precision_score,recall_score
import numpy as np
import warnings
warnings.filterwarnings("ignore")

train_file_nameA0='TrainData/train_A0_buffer.csv'
train_file_nameA1='TrainData/train_A1_buffer.csv'
train_file_nameA2='TrainData/train_A2_buffer.csv'
train_file_nameA3='TrainData/train_A3_buffer.csv'

A0=pd.read_csv(train_file_nameA0)
A1=pd.read_csv(train_file_nameA1)
A2=pd.read_csv(train_file_nameA2)
A3=pd.read_csv(train_file_nameA3)

Buffer_Test_List = [A0, A1, A2, A3]

train_file_nameA0='TrainData/train_A0_resolution.csv'
train_file_nameA1='TrainData/train_A1_resolution.csv'
train_file_nameA2='TrainData/train_A2_resolution.csv'
train_file_nameA3='TrainData/train_A3_resolution.csv'

A0=pd.read_csv(train_file_nameA0)
A1=pd.read_csv(train_file_nameA1)
A2=pd.read_csv(train_file_nameA2)
A3=pd.read_csv(train_file_nameA3)
Resolution_Test_List = [A0, A1, A2, A3]

label_list=["Status", "BufferWarning", "Resolution"]
acc_all = []
pre_all=[]
rec_all=[]
bfw_pre,bfw_rec = np.zeros((2,)) ,np.zeros((2,))
bfs_pre,bfs_rec = np.zeros((4,)) ,np.zeros((4,))
reso_pre,reso_rec = np.zeros((6,)) ,np.zeros((6,))
print('Testing')
for i in range(4):
    acc_item = []
    for j in range(-3,0):
        if j==-1:
            test_data = Resolution_Test_List[(i + 3) % 4]
        else:
            test_data = Buffer_Test_List[(i + 3) % 4]
        X_test = pd.concat([test_data.iloc[:, :-10], test_data.iloc[:, 125:127]], axis=1)
        Y_test = test_data.iloc[:, j]
        rf=joblib.load(f'Model/RFModel_A{i}A{(i+1)%4}A{(i+2)%4}_{label_list[j]}.pkl')
        Y_pred = rf.predict(X_test)
        accuracy = accuracy_score(Y_pred, Y_test)
        precision = precision_score(Y_pred, Y_test, average=None)
        recall = recall_score(Y_pred, Y_test, average=None)
        if j==-3:
            bfw_pre += precision
            bfw_rec += recall
        if j==-2:
            bfs_pre += precision
            bfs_rec += recall
        if j==-1:
            if precision.shape[0] == 7:
                reso_pre += precision[0:6]
                reso_rec += recall[0:6]
            else:
                reso_pre += precision
                reso_rec += recall
        print(f'A{i},A{(i+1)%4},A{(i+2)%4} as train data, A{(i+3)%4} as test data, label = {label_list[j]},accuracy = {round(accuracy,2)}')
        acc_item.append(accuracy)
    acc_all.append(acc_item)
acc_mat = np.array(acc_all)
paper_accuracy = np.array([0.92,0.842,0.669])
my_accuracy = np.average(acc_mat,axis=0)
error = (paper_accuracy - my_accuracy)/paper_accuracy
print('\n--------------|---------------|---------------|-----------|')
print(f'Type\t\t  |BufferWarning  |BufferStatus   |Resolution |')
print('--------------|---------------|---------------|-----------|')
print(f'Paper Accuracy|{round(paper_accuracy[0],3)}\t\t\t  |{round(paper_accuracy[1],3)}\t\t  |{round(paper_accuracy[2],3)}\t  |')
print('--------------|---------------|---------------|-----------|')
print(f'My Accuracy   |{round(my_accuracy[0],3)}\t\t  |{round(my_accuracy[1],3)}\t\t  |{round(my_accuracy[2],3)}\t  |')
print('--------------|---------------|---------------|-----------|')
print(f'Error         |{round(error[0],3)}\t\t  |{round(error[1],3)}\t\t  |{round(error[2],3)}\t  |')
print('--------------|---------------|---------------|-----------|')
bfw_pre,bfw_rec = bfw_pre/4,bfw_rec/4
bfs_pre,bfs_rec = bfs_pre/4,bfs_rec/4
reso_pre,reso_rec = reso_pre/4,reso_rec/4
print(pd.DataFrame(np.vstack((bfw_pre,bfw_rec)).T,columns=["Recall","Precision"]))
print(pd.DataFrame(np.vstack((bfs_pre,bfs_rec)).T,columns=["Recall","Precision"]))
print(pd.DataFrame(np.vstack((reso_pre,reso_rec)).T,columns=["Recall","Precision"]))