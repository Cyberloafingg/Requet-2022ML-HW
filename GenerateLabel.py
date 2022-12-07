import time
import pandas as pd
import glob
import numpy as np
import concurrent.futures

Dataset_List = ['A0','A1','A2','A3']
# Dataset_List = ['A0']
Datasets_Folder = "RequetDataSetNew"
Label_Folder = "LabelDataSet"
### 用来记录
Num = [0 for _ in range(0, 4)]
Sum = 0

MinTime_stall = 10
Thr_ss = 15
Resolution_List = ['q144p', 'q240p', 'q360p', 'q480p', 'q720p', 'q1080p', 'q1440p', 'q2160p']
Status_List = ['Stall', 'Steady State', 'Buffer Decay', 'Buffer Increase']

Stall_Threshold = 0.08
Delta = 0.0001
Epsilon = 0.15
T_smooth = 15
T_slope = 5
Buff_ss = 10
BuffWarningThresh = 20

def smooth_status(status_, m_t):
    status_smooth = status_.copy()
    now_index = 0
    # last_index = 0
    while now_index < len(status_smooth):
        if status_smooth[now_index] == 0:
            last_index = now_index
            end = min(len(status_smooth), now_index + MinTime_stall * 10 + 1)
            for j in range(now_index + 1, end):
                if status_smooth[j] == 0:
                    last_index = j
            for j in range(now_index + 1, last_index + 1):
                status_smooth[j] = 0
            if last_index != now_index:
                now_index = last_index
            else:
                now_index = now_index + 1
        else:
            now_index = now_index + 1

    now_index = 0
    while now_index < len(status_smooth):
        if status_smooth[now_index] == 1:
            last_index = now_index
            end = min(len(status_smooth), now_index + MinTime_stall * 10 + 1)
            for j in range(now_index + 1, end):
                if status_smooth[j] == 1:
                    last_index = j
            for j in range(now_index + 1, last_index + 1):
                status_smooth[j] = 1
            if last_index != now_index:
                now_index = last_index
            else:
                now_index = now_index + 1
        else:
            now_index = now_index + 1

    num = [0 for _ in range(len(status_smooth))]
    num[0] = 1
    for now_index in range(1, len(status_smooth)):
        if status_smooth[now_index] == 1:
            if status_smooth[now_index - 1] == 1:
                num[now_index] = num[now_index - 1] + 1
            else:
                num[now_index] = 1
                if num[now_index - 1] <= Thr_ss * 10:
                    for j in range(now_index - 1, -1, -1):
                        if status_smooth[j] == 1:
                            status_smooth[j] = 3 if m_t[j] >= 0 else 2
                        else:
                            break

    return status_smooth

def generate_csv():
    for datasets in Dataset_List:
        dataset_folder = f'{Label_Folder}/{datasets}/'  # 寻找到已经存为CSV的文件夹，在test_data下
        files = glob.glob(dataset_folder + '*_merged.csv')
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            executor.map(cal_label, files)

def cal_label(file):
    global Sum
    file_id = file.split('.')[0]
    df = pd.read_csv(file, low_memory=False)
    hat_b = {}
    m = []
    status = []
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
                                        [(numpy_RelativeTime >= (i - T_smooth - Delta))
                                        & (numpy_RelativeTime <= (i + T_smooth + Delta))]
                                )
    maxTime = round(numpy_RelativeTime.max() * 10) / 10
    for i in range(len(numpy_RelativeTime)):
        if numpy_BufferValid[i] == "-1":
            continue
        if i > 0:
            if numpy_EpochTime[i] == numpy_EpochTime[i - 1] or 0 == numpy_EpochTime[i - 1]:
                continue
        new_row = []
        new_row.append(numpy_EpochTime[i])
        t = numpy_RelativeTime[i]
        t_slope_1 = round((t + T_slope) * 10) / 10
        t_slope_2 = round((t - T_slope) * 10) / 10
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
        m.append(mt)
        b_t = numpy_BufferHealth[i]
        # BuffWarningThresh 以20作为分类标准 第71:6页
        if b_t < BuffWarningThresh:
            new_row.append(1)
            # np.append(new_row,1)
        else:
            new_row.append(0)
        if b_t < Stall_Threshold:
            state = 0
        elif -Epsilon <= mt <= Epsilon and b_t > Buff_ss:
            state = 1
        elif mt < 0:
            state = 2
        else:
            state = 3
        Sum = Sum + 1
        Num[state] = Num[state] + 1
        new_row.append(state)
        status.append(state)
        new_row.append(Resolution)
        array_label.append(new_row)
    df_new = pd.DataFrame(array_label, columns=["EpochTime", "BuffWarning", "status", "Resolution"])
    status = smooth_status(status, m)
    df_new['status'] = status
    df_new.to_csv(file_id + '_label.csv', index=None, header=True)
    print(file_id + '_tag.csv')

if __name__ == '__main__':
    print("Begin")
    start = time.time()
    generate_csv()
    end = time.time()
    print(f"Use {end - start}s")
