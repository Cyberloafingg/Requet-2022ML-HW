import time
import pandas as pd
import glob
import numpy as np
import concurrent.futures

###
Dataset_List = ['A0', 'A1', 'A2', 'A3']
Datasets_Folder = "RequetDataSetNew"
Label_Folder = "LabelDataSet"
Resolution_List = ['q144p', 'q240p', 'q360p', 'q480p', 'q720p', 'q1080p', 'q1440p', 'q2160p']
Status_List = ['Stall', 'Steady State', 'Buffer Decay', 'Buffer Increase']

# 参数
MIN_TIME_STALL = 10
THR_SS = 15
STALL_THRESHOLD = 0.08
DELTA = 0.0001
EPSILON = 0.15
T_SMOOTH = 15
T_SLOPE = 5
BUFF_SS = 10
BUFF_WARNING_THRESHOLD = 20

SUM = 119 + 130 + 91 + 95
it = 0

# smooth 函数
def smooth_status(status_, m_t):
    smooth = status_.copy()
    n_idx = 0
    # 1.情况1 STALL是否不连续
    while n_idx < len(smooth):
        if smooth[n_idx] == 0:
            l_idx = n_idx
            end_idx = min(len(smooth), n_idx + MIN_TIME_STALL * 10 + 1)
            for j in range(n_idx + 1, end_idx):
                if smooth[j] == 0:
                    l_idx = j
            for j in range(n_idx + 1, l_idx + 1):
                smooth[j] = 0
            if l_idx != n_idx:
                n_idx = l_idx
            else:
                n_idx = n_idx + 1
        else:
            n_idx = n_idx + 1
    # 2.
    n_idx = 0
    while n_idx < len(smooth):
        if smooth[n_idx] == 1:
            l_idx = n_idx
            end_idx = min(len(smooth), n_idx + MIN_TIME_STALL * 10 + 1)
            for j in range(n_idx + 1, end_idx):
                if smooth[j] == 1:
                    l_idx = j
            for j in range(n_idx + 1, l_idx + 1):
                smooth[j] = 1
            if l_idx != n_idx:
                n_idx = l_idx
            else:
                n_idx = n_idx + 1
        else:
            n_idx = n_idx + 1

    num = [0 for _ in range(len(smooth))]
    num[0] = 1
    for n_idx in range(1, len(smooth)):
        if smooth[n_idx] == 1:
            if smooth[n_idx - 1] == 1:
                num[n_idx] = num[n_idx - 1] + 1
            else:
                num[n_idx] = 1
                if num[n_idx - 1] <= THR_SS * 10:
                    for j in range(n_idx - 1, -1, -1):
                        if smooth[j] == 1:
                            smooth[j] = 3 if m_t[j] >= 0 else 2
                        else:
                            break

    return smooth


def generate_csv():
    global it
    print(f'Generate Label:|',end='')
    for datasets in Dataset_List:
        dataset_folder = f'{Label_Folder}/{datasets}/'  # 寻找到已经存为CSV的文件夹，在test_data下
        files = glob.glob(dataset_folder + '*_merged.csv')
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            executor.map(cal_label, files)
    print(f'| Finish {SUM} File')

def cal_label(file):
    global it
    file_id = file.split('.')[0]
    df = pd.read_csv(file, low_memory=False)
    hat_b = {}
    m_list = []
    status_list = []
    array_label = []
    ## 要使用的存储df
    numpy_RelativeTime = np.array(df['RelativeTime'])
    numpy_BufferHealth = np.array(df['BufferHealth'])
    numpy_BufferValid = np.array(df["BufferValid"])
    numpy_EpochTime = np.array(df["EpochTime"])
    numpy_Resolution = np.array(df[Resolution_List])
    for i in numpy_RelativeTime:
        hat_b[round(i * 10) / 10] = np.median(
            numpy_BufferHealth
            [(numpy_RelativeTime >= (i - T_SMOOTH - DELTA))
             & (numpy_RelativeTime <= (i + T_SMOOTH + DELTA))]
        )
    maxTime = round(numpy_RelativeTime.max() * 10) / 10
    for i in range(len(numpy_RelativeTime)):
        if numpy_BufferValid[i] == "-1":
            continue
        if i > 0:
            if numpy_EpochTime[i] == numpy_EpochTime[i - 1] or \
                    0 == numpy_EpochTime[i - 1]:
                continue
        new_row = []
        new_row.append(numpy_EpochTime[i])
        t = numpy_RelativeTime[i]
        t_slope_1 = round((t + T_SLOPE) * 10) / 10
        t_slope_2 = round((t - T_SLOPE) * 10) / 10
        # 将t_slope卡在[0,maxTime]之间
        if t_slope_1 > maxTime:
            t_slope_1 = maxTime
        if t_slope_2 < 0:
            t_slope_2 = 0
        Resolution = 0
        for j in range(len(Resolution_List)):
            if numpy_Resolution[i, j] == 1:
                Resolution = j
                break
        mt = (hat_b[t_slope_1] - hat_b[t_slope_2]) / (t_slope_1 - t_slope_2)
        m_list.append(mt)
        b_t = numpy_BufferHealth[i]
        # BuffWarningThresh 以20作为分类标准 第71:6页
        if b_t < BUFF_WARNING_THRESHOLD:
            new_row.append(1)
            # np.append(new_row,1)
        else:
            new_row.append(0)
        if b_t < STALL_THRESHOLD:
            state = 0
        elif -EPSILON <= mt <= EPSILON and b_t > BUFF_SS:
            state = 1
        elif mt < 0:
            state = 2
        else:
            state = 3
        new_row.append(state)
        status_list.append(state)
        new_row.append(Resolution)
        array_label.append(new_row)
    df_new = pd.DataFrame(array_label, columns=["EpochTime", "BuffWarning", "status", "Resolution"])
    status_list = smooth_status(status_list, m_list)
    df_new['status'] = status_list
    df_new.to_csv(file_id + '_label.csv', index=None, header=True)
    it +=1
    if it % 7 == 0:
        print(f'*',end='')


if __name__ == '__main__':
    start = time.time()
    generate_csv()
    end = time.time()
    print("******* Generate Label Succeed! ********")
    print(f"Generate Label Use {end - start}s")
