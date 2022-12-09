## 程序说明
1. 采用了进程池进行进行并行处理数据
2. 通过`MergeFileProcess.py`对MergedFile数据进行处理，将文件转换为csv格式存储在LabelDataSet目录下
3. 通过`GenerateLabel.py`进行VideoStateLabeling，生成label
4. 通过`GenerateTrainData.py`进行ChunkDetection以及FeatureExtraction，生成Feature--Label按照论文方法对应的模型训练数据文件存储在TrainData中，由于Resolution的生成方式不一样，因此对于A0--A3四个文件生成了4*2=8个不同的模型训练数据文件
5. 训练模型放在了RF_Train的ipython文件中，采用四折交叉验证的方法生成了3*4=12组pkl模型
6. 通过`TestModel.py`进行对于模型性能的验证。



## 运行方法
1. 将 RequetDataSetNew 文件夹放入程序目录
2. 运行 main.py
   ```
   python -u "./main.py"
   ```
