## 程序说明
1. 采用了进程池进行进行并行处理数据
2. 通过`MergeFileProcess.py`对MergedFile数据进行处理，将文件转换为csv格式存储在LabelDataSet目录下
3. 通过`GenerateLabel.py`进行VideoStateLabeling，生成label
4. 通过`GenerateTrainData.py`进行ChunkDetection以及FeatureExtraction，生成Feature--Label按照论文方法对应的模型训练数据文件存储在TrainData中，由于Resolution的生成方式不一样，因此对于A0--A3四个文件生成了4*2=8个不同的模型训练数据文件
5. 训练模型放在了RF_Train的ipython文件中，采用四折交叉验证的方法生成了3*4=12组pkl模型
6. 通过`TestModel.py`进行对于模型性能的验证。
7. `main.py` 整合了上述2、3、4、6过程，用来生成“模型训练文件”，测试所需模型采用了在我本地生成的pkl模型(Model文件夹下)，当然您也可以重新运行`RF_Train.ipthon` 文件，覆盖我生成的模型，再进行测试。


## 运行方法
1. ```
   pip install -r requirements.txt
   ```
2. 将 RequetDataSetNew 文件夹放入程序目录
3. 运行 main.py,用来生成“模型训练文件”，该文件将被生成在TrainData文件夹下，以及获取预测结果。
   ```
   python -u "./main.py"
   ```
4. 在控制台中会输出与下方图片类似的结果，如果你需要使用在本机训练的模型，请运行`RF_train.ipython`文件，覆盖Model文件夹下的模型。然后再运行`TestModel.py`

## 结果
![这是图片](https://github.com/Cyberloafingg/Requet-2022ML-HW/blob/main/IMG/1.png)

