# 树莓派图像识别

`server/`文件夹下为电脑端Flask测试程序，`pi/`文件夹下为树莓派端实验示例程序（仅用于参考，准确率和性能上不作任何保证），`converter/`文件夹下为一个TensorFlow Lite模型转换示例。

## 整体架构

电脑端flask server和浏览器界面、树莓派分别建立socket连接。浏览器初始化后重复以下操作：

1. 浏览器通知server图片已更新
2. server等待0.1s后（树莓派获取图像有延迟，可以修改等待时间`display_delay`）通知树莓派进行图像识别，并开始计时
3. 树莓派将识别结果和系统信息通过post方法传回server
4. server检查结果、计算用时和准确率
5. server通知浏览器更新
6. 浏览器更新结果数据和图像

![workflow](./md-img/workflow.png)

## 安装

### PC端

+ 安装Flask、Flask-SocketIO等必要库

  ```
  pip install Flask
  pip install Flask-SocketIO
  ```

### 树莓派

+ 安装并运行mjpg-streamer，获取树莓派视频流

  + 安装：需要先安装依赖库，然后下载源码编译，参考

    [https://github.com/cncjs/cncjs/wiki/Setup-Guide:-Raspberry-Pi-%7C-MJPEG-Streamer-Install-&-Setup-&-FFMpeg-Recording](https://github.com/cncjs/cncjs/wiki/Setup-Guide:-Raspberry-Pi-|-MJPEG-Streamer-Install-&-Setup-&-FFMpeg-Recording)

  - 运行：

    ```
    /usr/local/bin/mjpg_streamer -i "input_uvc.so -r 640x360 -d /dev/video0 -f 30" -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"
    ```

  - 640x360表示推流分辨率，8080表示端口号，都可以自行调整，适当调低分辨率可以减少延迟

  - 浏览器打开`http://{pi_ip}:8080`即为mjpg-streamer自带页面，想直接获取视频内容可以在html中使用标签`<img src=http://{pi_ip}:8080/?action=stream />`

+ 安装pip3、numpy等必要依赖

  + 建议pip3 install时用whl文件安装，[https://www.piwheels.org/packages.html](https://www.piwheels.org/packages.html)上可找到对应的whl

+ 安装tf lite解释器：[https://www.tensorflow.org/lite/guide/python#install_tensorflow_lite_for_python](https://www.tensorflow.org/lite/guide/python#install_tensorflow_lite_for_python)

+ 安装opencv

  + 直接pip3 install，python3可能会出现ImportError，需手动安装出错的依赖
  + 一种可能的安装办法：参考[https://zhuanlan.zhihu.com/p/46032511](https://zhuanlan.zhihu.com/p/46032511)安装apt依赖后，用whl文件安装opencv-python，剩下的依赖再补装一下

## 运行

### ip设置

+ 获取树莓派ip地址`pi_ip`和电脑端ip地址`server_ip`
+ 在`server/app.py`中修改`pi_ip`
+ 在`pi/classify_picamera.py`中修改`server_ip`

### PC端

+ `server/`文件夹下运行

  ```
  flask run --host='0.0.0.0'
  ```

  在任意终端设备浏览器上打开`http://{server_ip}:5000/`显示图片界面。

### 树莓派

+ 将`pi/`文件夹拷贝至树莓派，运行

  ```
  python3 classify_picamera.py --model model.tflite --labels synset_words.txt
  ```

+ 树莓派对准浏览器界面上的图像，刷新浏览器后开始运行

## 说明

+ FPS的计算：树莓派传回的FPS表示进行一帧图像识别的帧率，server计算的FPS_ALL表示整个识别循环进行一轮的帧率（包括网络延迟和`display_delay`），`display_delay`可以根据系统性能自行修改。

+ 验证集包含100张图片，在界面上随机显示，全部显示一遍后重新开始下一轮随机。

+ 测试集包含100张图片，同样为随机显示。测试集未公开，检查时只需要将测试集的图像和GT拷贝至电脑端`server/static`文件夹，并在`server/app.py`中修改mode参数为"test"即可。

+ 注意：存在多种版本的index和label对应关系，ILSVRC2012的label版本和Caffe提供版本的不同。
  + 在本实验示例程序中用到的MobileNet使用的是Caffe版本的label

    [https://github.com/HoldenCaulfieldRye/caffe/blob/master/data/ilsvrc12/synset_words.txt](https://github.com/HoldenCaulfieldRye/caffe/blob/master/data/ilsvrc12/synset_words.txt)

  + 为了统一，测试程序中检查的是：识别结果和Ground Truth的**synset标签**是否吻合
  
+ 在使用预训练模型时，注意输入数据的格式范围、输出index和label之间的对应关系

