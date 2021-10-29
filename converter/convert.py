#encoding=utf-8
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.applications import MobileNet, MobileNetV2, VGG16
from tensorflow import lite


input_shape=(224, 224, 3)
model = MobileNet(input_shape=input_shape, weights='imagenet')

converter = lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open('model.tflite', 'wb') as f:
    f.write(tflite_model)
