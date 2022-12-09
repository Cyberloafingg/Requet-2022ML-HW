import glob
import os
import concurrent.futures
import time
# 清理原始数据
# 规范：全局变量使用首字母大写
Dataset_List = ['A0','A1','A2','A3']
Datasets_Folder = "RequetDataSetNew"
Label_Folder = "LabelDataSet"
COLS = ['RelativeTime', 'PacketsSent', 'PacketsReceived', 'BytesSent', 'BytesReceived']
Network_Info_Num = 26 # 一共26个NetworkINFO
# 已知的文件数量，最为后续处理txt的验证
Data_Num_In_Folder = {
    'A0':95,
    'A1':130,
    'A2':91,
    'A3':119
}


def construct_columns():
    for i in range(0, Network_Info_Num):
        ss = str(i)
        Network_Info = ['IPSrc' + ss,
                        'IPDst' + ss,
                        'Protocol' + ss,
                        'PacketsSent' + ss,
                        'PacketsReceived' + ss,
                        'BytesSent' + ss,
                        'BytesReceived' + ss]
        COLS.extend(Network_Info)
    COLS.extend(['Buffering', 'Paused', 'Playing', 'CollectData']);
    COLS.extend(['EpochTime','StartTime', 'PlaybackProgress', 'Length']);
    COLS.extend(['UnlabelledQuality', 'q144p', 'q240p','q360p', 'q480p', 'q720p', 'q1080p', 'q1440p', 'q2160p']);
    COLS.extend(['BufferHealth', 'BufferProgress', 'BufferValid'])
    # 验证构建正确性
    TARGET_NUM_COLS = 5 + 7 * 26 + (4 + 4 + 9 + 3)
    if len(COLS) != TARGET_NUM_COLS:
        raise Exception(f"Error number of columns {len(COLS)}, targat columns is {TARGET_NUM_COLS} ")
    else:
        print(f"Succeed to construct COL:{len(COLS)}")



def clean_work_dir():
    for datasets in Dataset_List:
        dataset_folder = f'{Datasets_Folder}/{datasets}/MERGED_FILES/'
        files = glob.glob(dataset_folder + '*.csv')
        for file in files:
            os.remove(file)

def conactenat(combination):
    file , dataset =  combination
    COLS_file_name = f"cols.txt"
    csv_filename = f"{Label_Folder}/{dataset}/{os.path.split(file)[1]}".split('.')[0] + ".csv"
    origin_file = open(file, "rt")
    csv_file = open(csv_filename, "wt")
    cols_file = open(COLS_file_name,"rt")
    for line in cols_file:
        csv_file.write(line)
    for line in origin_file:
        if not line.isspace():
            csv_file.write(line.replace('[', '').replace(']', ''))
    origin_file.close()
    csv_file.close()
    cols_file.close()



def generate_label_file():
    with open("cols.txt", "w") as text_file:
        text_file.write(",".join(COLS)+"\n")
    for datasets in Dataset_List:
        dataset_folder = f'{Datasets_Folder}/{datasets}/MERGED_FILES/'
        files = glob.glob(dataset_folder + '*_*_merged.txt')
        if len(files) != Data_Num_In_Folder[datasets]:
            raise Exception(f"Error File Num,Please Check Folder :{dataset_folder}")
        else:
            print(f"Folder : {dataset_folder} , File Num : {len(files)}")
        os.system(f"md {Label_Folder}\\{datasets}")
        # 将组合参数传入
        combination = []
        for i in files:
            combination.append((i,datasets))
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            executor.map(conactenat, combination)
    print("******Concatenated All Folder!*******")


if __name__ == '__main__':
    #### 生成label_file
    clean_work_dir()
    construct_columns()
    start = time.time()
    generate_label_file()
    end = time.time()
    print(f"Use {end - start}s")