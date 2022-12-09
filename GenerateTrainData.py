import dpkt
import numpy as np
import socket
import pandas as pd
import csv
import glob
import os
from tqdm import tqdm
import time
import concurrent.futures

np.set_printoptions(suppress=True, precision=20, threshold=10, linewidth=40)

GET_THRESH = 300  # bytes
DOWN_THRESH = 300  # bytes
VIDEO_CHUNK_GETSIZE = 700  # bytes
AUDIO_CHUNK_GETSIZE = 600  # bytes
INTERVAL = 50
Dataset_List = ['A0','A1','A2','A3']
TRAIN_DATA_DIR = "TrainData"


class Chunk():
    def __init__(self, GetTimestamp=0, GetSize=0, DownStart=0, DownEnd=0, DownSize=0, type=0, GetProtocol="",
                 serverIP=""):
        self.GetTimestamp = GetTimestamp  # 发送请求的时间戳
        self.GetSize = GetSize  # Get请求的长度
        self.DownStart = DownStart  # 块的第一个下行包的时间戳
        self.DownEnd = DownEnd  # 块的最后一个下行包的时间戳
        self.DownSize = DownSize  # 块的所有下行包的大小之和
        self.type = type  # 类型：视频或音频
        self.GetProtocol = GetProtocol  # 协议
        self.serverIP = serverIP

    def getGetTimestamp(self):
        return self.GetTimestamp

    def getDownEnd(self):
        return self.DownEnd

    def getServerIP(self):
        return self.serverIP

    def getGetSize(self):
        return self.GetSize

    def setType(self, newType):
        self.type = newType

    def __lt__(self, other):
        self_small = True
        A = self.GetTimestamp
        B = other.GetTimestamp
        self_small = A < B
        return self_small

    def detectAV(self):
        # 论文里是根据GetSize, DownSize, GetProtocol来区分视频块，音频块和后台流量的
        flag = 0
        if self.DownSize <= 80 * 1024:
            flag = 2
        else:
            if abs(self.GetSize - VIDEO_CHUNK_GETSIZE) > abs(self.GetSize - AUDIO_CHUNK_GETSIZE):  # 判断这个大小更接近视频块还是音频块
                flag = 0
            else:
                flag = 1
        # 基于协议号的筛选
        return flag

    def __str__(self):
        return f"{self.serverIP} {self.GetTimestamp} {self.GetSize} {self.DownStart} {self.DownEnd} {self.DownSize} {self.type} {self.GetProtocol}"

    def __repr__(self):
        return f"{self.serverIP} {self.GetTimestamp} {self.GetSize} {self.DownStart} {self.DownEnd} {self.DownSize} {self.type} {self.GetProtocol}"


def inet_to_str(inet):
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except:
        return False


def isUplink(src):
    return src[0:7] == '192.168'


def ChunkDetection(filename):
    # 解析pcap文件
    # print("Reading pcap file...")

    # 读入pcap文件
    f = open(filename, 'rb')
    pcap = dpkt.pcap.Reader(f)

    # meta_time = 0
    ii = 0
    # pcap是Reader类，无法切片，目前先这样写
    # for ts, buf in pcap:
    #     ii += 1
    #     if ii == 1:
    #         meta_time = ts
    #         break
    # end_time = meta_time
    chunks = {}
    chunksValue = []
    downFlag = {}  # 用于标识是不是第一个下行报文

    # print("Parsing pcap file...")

    times = []
    ip_srcs = []
    ip_dsts = []
    ip_lens = []
    ip_ihls = []
    ip_protos = []
    for ts, buf in pcap:
        # 这里也是对没有IP段的包过滤掉
        eth = dpkt.ethernet.Ethernet(buf)
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            continue
        # ts是时间戳
        times.append(ts)
        ip = eth.data
        ip_src = inet_to_str(ip.src)  #
        ip_dst = inet_to_str(ip.dst)  #
        ip_srcs.append(ip_src)  # src
        ip_dsts.append(ip_dst)  # dst
        ip_lens.append(ip.len)  # len
        ip_protos.append(ip.p)  # proto:协议号tcp是6
        ip_ihls.append(ip.hl)  # ihl
    first_end_time = (times[0], times[-1])
    sumGetSize = 0
    for n in range(len(ip_srcs)):
        ipSrc = ip_srcs[n]
        ipDst = ip_dsts[n]
        ipSize = ip_lens[n] - ip_ihls[n] * 4
        ipTime = times[n]
        ipProto = ip_protos[n]
        # end_time = ipTime
        if isUplink(ipSrc) and ipSize > GET_THRESH:
            # 上行包，2种情况：（1）已经出现过的，则处理上一个发往这个站点的块，并初始化新块；（2）没有出现过，初始化新块
            if ipDst in chunks:  # 意味着以这一ip地址为目的地址的块已经结束，以这一ip地址为目的地址的块马上开始
                # 筛选：刚刚结束的块是否是音频或视频块
                avFlag = chunks[ipDst].detectAV()
                if not avFlag == 2:  # 音频块
                    sumGetSize += chunks[ipDst].getGetSize()
                    chunksValue.append(chunks[ipDst])
                else:  # 后台流量
                    chunks.pop(ipDst)  # 抛弃这个块
                    downFlag.pop(ipDst)
            # 初始化新块
            chunks[ipDst] = Chunk(GetTimestamp=ipTime, GetSize=ipSize, GetProtocol=ipProto, serverIP=ipDst)
            downFlag[ipDst] = False
        elif not isUplink(ipSrc) and ipSize > DOWN_THRESH:
            if ipSrc in chunks:
                # 下行包，2种情况：（1）是Get请求的第一个下行包，记录时间，更新大小和时间；（2）不是Get请求的第一个下行包，更新大小和时间
                if not downFlag[ipSrc]:
                    chunks[ipSrc].DownStart = ipTime  # 收到第一个下行包的时间
                    downFlag[ipSrc] = True
                chunks[ipSrc].DownEnd = ipTime
                chunks[ipSrc].DownSize += ipSize
                chunks[ipSrc].protocol = ipProto

    for c in chunks.values():
        avFlag = c.detectAV()
        if not avFlag == 2:  # 音频块
            sumGetSize += c.getGetSize()
            chunksValue.append(c)

    # 区分音频块和视频块
    chunkNum = len(chunksValue)
    if chunkNum == 0:
        ave_GetSize = 0
    else:
        ave_GetSize = sumGetSize / chunkNum
    for s_chunk in chunksValue:
        if s_chunk.getGetSize() > ave_GetSize:
            s_chunk.setType(0)
        else:
            s_chunk.setType(1)

    return chunkNum, chunksValue, first_end_time


def getChunkMetrics(chunkNum, chunksValue):
    sortChunks = sorted(chunksValue)
    # 顺序：'start_time', 'type', 'ttfb', 'download_time', 'end_time', 'get_size', 'chunk_size'
    output_data = np.zeros((chunkNum, 7))
    i = 0
    for c in sortChunks:
        start_time = c.GetTimestamp
        ttfb = c.DownStart - start_time
        download_time = c.DownEnd - c.DownStart
        end_time = c.DownEnd
        get_size = c.GetSize
        chunk_size = c.DownSize
        type = c.type
        output_data[i] = np.array([start_time, type, ttfb, download_time, end_time, get_size, chunk_size])
        i += 1
    return output_data



def getFeature(epoch_msec, cm, first_end_time):
    t = epoch_msec / 1000
    if t < first_end_time[0] or t > first_end_time[1]:
        return None
    s = []
    start_time = 0
    type = 1
    ttfb = 2
    download_time = 3
    end_time = 4
    get_size = 5
    chunk_size = 6
    flag1 = True
    last_chunk = []
    for w in range(1, 21):
        period = w * 10.0
        if t - period < first_end_time[0]:
            total_number_of_chunks_v = -1
            avg_chunk_size_v = -1
            download_time_v = -1
            total_number_of_chunks_a = -1
            avg_chunk_size_a = -1
            download_time_a = -1
        else:
            is_out_border = (cm[:, end_time] > t - period) & (cm[:, start_time] < t)
            if flag1 and len(cm[is_out_border]) != 0:
                last_chunk = cm[is_out_border]
                flag1 = False
            total_number_of_chunks_v = cm[(cm[:, type] == 0) & is_out_border].shape[0]
            if total_number_of_chunks_v == 0:
                avg_chunk_size_v = 0
            else:
                avg_chunk_size_v = cm[:, chunk_size][
                    (cm[:, type] == 0) & (cm[:, end_time] > t - period) & (cm[:, start_time] < t)].mean()
            download_time_v = cm[:, download_time][(cm[:, type] == 0) & is_out_border].sum()
            total_number_of_chunks_a = cm[(cm[:, type] == 1) & is_out_border].shape[0]
            if total_number_of_chunks_a == 0:
                avg_chunk_size_a = 0
            else:
                avg_chunk_size_a = cm[:, chunk_size][
                    (cm[:, type] == 1) & (cm[:, end_time] > t - period) & (cm[:, start_time] < t)].mean()
            download_time_a = cm[:, download_time][(cm[:, type] == 1) & is_out_border].sum()
        s += [total_number_of_chunks_v, avg_chunk_size_v, download_time_v,
              total_number_of_chunks_a, avg_chunk_size_a, download_time_a]
    if not flag1:
        s += list(last_chunk[-1])
    if not len(s) == 127:
        s += [-1, -1, -1, -1, -1, -1, 1]
    return s


def generate_train_data(dataset):
    train_data_buffer = []
    train_data_resolution = []
    dataset_folder = f'LabelDataSet/{dataset}/'
    files = glob.glob(dataset_folder + '*_label.csv')
    # cnt=0
    for i in tqdm(range((len(files))), desc=f'Generating {dataset} training data', ncols=80, colour='blue'):
        file_name = files[i]
        file = pd.read_csv(file_name).to_numpy()
        file_origin = os.path.split(file_name)[1].split('/')[-1][:-17]
        feature_file = f'RequetDataSetNew/{dataset}/PCAP_FILES/{file_origin}.pcap'
        # 1. chunkDetection
        chunkNum, chunksValue0, fe_time = ChunkDetection(feature_file)
        # 2. chunkMetrics
        output = getChunkMetrics(chunkNum, chunksValue0)
        lable_num = file.shape[0]
        for i in range(0, lable_num, INTERVAL):
            feature = getFeature(file[i, 0], output, fe_time)
            if not feature:
                continue
            # feature.append(file_name + "-" + str(file.iloc[i, 0]))
            feature.extend(file[i, 1:])
            train_data_buffer.append(feature)
            if feature[121] == 0:
                train_data_resolution.append(feature)
    # buffer
    train_data_buffer_file = open(f'{TRAIN_DATA_DIR}/train_{dataset}_buffer.csv', 'w', newline='')
    writer = csv.writer(train_data_buffer_file)
    keys = ['f' + str(i) for i in range(120)]
    keys.extend(['start_time', 'type', 'ttfb', 'download_time', 'end_time', 'get_size', 'chunk_size'])
    keys.extend(['status', 'BuffWarning', 'Resolution'])
    writer.writerow(keys)
    for i in train_data_buffer:
        writer.writerow(i)
    train_data_buffer_file.close()

    # resolution
    train_data_resolution_file = open(f'{TRAIN_DATA_DIR}/train_{dataset}_resolution.csv', 'w', newline='')
    writer = csv.writer(train_data_resolution_file)
    keys = ['f' + str(i) for i in range(120)]
    keys.extend(['start_time', 'type', 'ttfb', 'download_time', 'end_time', 'get_size', 'chunk_size'])
    keys.extend(['status', 'BuffWarning', 'Resolution'])
    writer.writerow(keys)
    for i in train_data_resolution:
        writer.writerow(i)
    train_data_resolution_file.close()



if __name__ == '__main__':
    starting = time.time()
    os.system(f"mkdir {TRAIN_DATA_DIR}")
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(generate_train_data, Dataset_List)
    ending = time.time()
    print(f'Use {ending - starting}s')
