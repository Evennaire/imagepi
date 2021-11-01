from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import io
import time
import threading
import numpy as np

from PIL import Image
from tflite_runtime.interpreter import Interpreter

from cv2 import VideoCapture, CAP_PROP_BUFFERSIZE
import os
import requests
import json
import time
import socketio

server_ip = "*.*.*.*"
sio = socketio.Client()
sio.connect(f"http://{server_ip}:5000")

post_url = f"http://{server_ip}:5000/result"

cap = VideoCapture(f"http://localhost:8080/?action=stream")
cap.set(CAP_PROP_BUFFERSIZE, 3)

ret = False
frame = 0
tmp = 0

labels = None
interpreter = None
camera = None


def getCPUuse():
    return os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip()

def getMemuse():
    return os.popen("free -m | grep Mem").readline().strip().split()[2]


def load_labels(path):
    with open(path, 'r') as f:
        return {i: line.strip() for i, line in enumerate(f.readlines())}


def set_input_tensor(interpreter, image):
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = (np.array(image) / 127.5) - 1 #input scale


def classify_image(interpreter, image, top_k=1):
    """Returns a sorted array of classification results."""
    set_input_tensor(interpreter, image)
    interpreter.invoke()
    output_details = interpreter.get_output_details()[0]
    output = np.squeeze(interpreter.get_tensor(output_details['index']))
  
    # If the model is quantized (uint8 data), then dequantize the results
    if output_details['dtype'] == np.uint8:
      scale, zero_point = output_details['quantization']
      output = scale * (output - zero_point)

    ordered = np.argpartition(-output, top_k)
    return [(i, output[i]) for i in ordered[:top_k]]


@sio.on('pi')
def on_message(data):
    print("message received!")
    received_time = time.time()
    # while not ret:
    #   pass

    _, height, width, _ = interpreter.get_input_details()[0]['shape']
    image = Image.fromarray(frame.astype('uint8')).convert('RGB').resize((width, height), Image.ANTIALIAS)

    results = classify_image(interpreter, image)
    label_id, prob = results[0]
    label_id += 1 # fix label index
    annotate_text = '%s %.2f' % (labels[label_id], prob)
    fps = 1 / (time.time() - received_time)
    cpu = getCPUuse()
    mem = getMemuse()
    data = {"res": labels[label_id], 
            "fps": fps,
            "cpu": cpu,
            "mem": mem}
    res = requests.post(url=post_url,data=data)
    print(data)



def get_frame():
    global ret, frame, tmp
    while True:
        ret, frame = cap.read()


def main():
    global ret, frame, tmp, labels, interpreter, camera
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--model', help='File path of .tflite file.', required=True)
    parser.add_argument(
        '--labels', help='File path of labels file.', required=True)
    args = parser.parse_args()

    labels = load_labels(args.labels)

    interpreter = Interpreter(args.model)
    interpreter.allocate_tensors()


if __name__ == '__main__':
    t = threading.Thread(target=get_frame)
    t.setDaemon(True)
    t.start()
    main()
