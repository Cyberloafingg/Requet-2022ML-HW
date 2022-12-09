import os
import time

if __name__ == '__main__':
    start = time.time()
    os.system('python -u ./MergeFileProcess.py')
    os.system('python -u ./GenerateLabel.py')
    os.system('python -u ./GenerateTrainData.py')
    end = time.time()
    print(f'TrainData Generated , Total Use{end - start}s')
    print('######################################################')
    print('###################      Result     ##################')
    print('######################################################')
    os.system('python -u ./TestModel.py')