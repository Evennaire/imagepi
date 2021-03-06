from flask import Flask, request, render_template, Response, url_for
from flask_socketio import SocketIO, emit
import random
import os
import time

pi_ip = "*.*.*.*"
mode = "valid"
display_delay = 0.1


label_url = f"./static/{mode}.txt"
display_seq = list(range(1, 101))
random.shuffle(display_seq)
display_idx = 0
start_time = time.time()
test_num = 0
true_num = 0
labels = {}
for line in open(label_url).readlines():
    [idx, label, text] = line.strip().split(' ', 2)
    labels[int(idx)] = [label, text]

start_flag = False
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug = True
socketio = SocketIO(app)


def send_msg(pred=-1, gt=-1, correct=-1, fps_all=-1, acc=-1, test_num=-1, cpu=-1, mem=-1, fps=-1):
    # 通知浏览器更新显示结果，同时更新图片
    global display_idx
    display_idx = (display_idx + 1) % 100
    img_url = url_for('static', filename = f'{mode}/{mode}_{display_seq[display_idx]}.jpeg')
    socketio.emit('res', {'pred':pred, 'gt':gt, 'correct':correct, 'img_url': img_url, 'fps_all': fps_all, 'acc': acc, 'test_num': test_num, 'cpu': cpu, 'mem': mem, 'fps':fps})


@app.route("/")
def index():
    res = "Initializing..."
    error = None
    return render_template('index.html', pi_ip=str(pi_ip), res=res, error=error)


@app.route("/result", methods=['POST'])
def result():
    # 收到树莓派传来的分类结果
    global start_time, test_num, true_num
    error = None
    res = -1
    fps_all = 1 / (time.time() - start_time)
    start_time = time.time()
    if request.method == 'POST':
        if 'res' in request.form.keys():
            res = request.form['res']
            fps = float(request.form['fps'])
            cpu = request.form['cpu']
            mem = request.form['mem']
            dp = int(request.form['idx'])
            res_label, res_text = res.split(' ', 1)
            res_correct = (res_label == labels[display_seq[dp]][0])
            test_num += 1
            true_num = true_num + 1 if res_correct else true_num
            gt = " ".join(labels[display_seq[dp]])
            send_msg(res, gt, str(res_correct), f"{fps_all:0.2f}", f"{true_num / test_num:0.4f}", test_num, cpu, mem, f"{fps:0.2f}")
            time.sleep(display_delay) # 延时display_delay后通知树莓派
            socketio.emit('pi', f"new image {display_idx}")  # 向树莓派发送pi信号说明图片已更新
        else:
            error = 'invalid post'
    return "ok"

@socketio.on('connected')
def handle_message(message):
    # 浏览器连接成功
    print('received message: ' + message)
    send_msg()

# @socketio.on('pi')
# def handle_message(message):
#     # 收到浏览器更新图片的通知，等待display_delay(s)后通知树莓派识别图像
#     global start_time, display_delay
#     time.sleep(display_delay)
#     socketio.emit('pi', "new image")
#     # start_time = time.time()

# 手动向树莓派发送更新提示
@socketio.on('ask')
def ask_pi(message):
    global start_flag
    if not start_flag:
        socketio.emit('pi', f"new image {display_idx}")
        start_flag = True


@socketio.on('reset')
def handle_message(message):
    # 收到浏览器事件：重置
    global test_num, true_num
    print('received message: ' + message)
    test_num = 0
    true_num = 0