# ## Import Standard Python
import os
import sys
import time
# ## 
import numpy as np
from threading import Thread
import tensorflow as tf
from PIL import Image
import cv2

# ## Object detection imports
# Here are the imports from the object detection module.
from utils import label_map_util
from utils import visualization_utils as vis_util
# ## Import TTS module
import pyttsx3
engine = pyttsx3.init()


# Define VideoStream class to handle streaming of video from webcam in separate processing thread
# Source - Adrian Rosebrock, PyImageSearch: https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(1280,720),framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(1)
        # ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])    
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()
        # Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
    # Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return
            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
    # Return the most recent frame
        return self.frame

    def stop(self):
    # Indicate that the camera and thread should be stopped
        self.stopped = True
## End of class

MODEL_NAME = 'ssdlite_mobilenet_v2'
# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
# print("PATH_TO_CKPT=" + str(PATH_TO_CKPT))
# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('data', 'mscoco_label_map.pbtxt')
# print("PATH_TO_LABELS=" + str(PATH_TO_LABELS))

NUM_CLASSES = 90

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.compat.v1.GraphDef()
    with tf.compat.v2.io.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

# ## Loading label map
# Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine
label_path = "/home/ahmed/Documents/Tensorflow/models/research/object_detection/"+MODEL_NAME+"/graph.pbtxt"
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(
                    label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)
# print("category_index= "+str(category_index)) #cateogry_index={1: {'id': 1, 'name': 'person'}, 2: {'id': 2, 'name': 'bicycle'}...etc}

print("0")
# Initialize video stream
videostream = VideoStream(resolution=(1280,720),framerate=30).start()
time.sleep(1)
imW = 1280
imH = 720
print("1")

# image_np = videostream.read()
# cv2.imshow('object detection', cv2.resize(image_np, (800, 600)))

with detection_graph.as_default():
    with tf.compat.v1.Session(graph=detection_graph) as sess:
        while True:
            # print("2")
            image_np = videostream.read()
            #o/p: frame
            # print("3")
            image_np_expanded = np.expand_dims(image_np, axis=0)
            # print("image_np_expanded= "+str(image_np_expanded))
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            # print("image_tensor= "+str(image_tensor))
            boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            # print("boxes= "+str(boxes))
            scores = detection_graph.get_tensor_by_name('detection_scores:0')
            # print("scores= "+str(scores))
            classes = detection_graph.get_tensor_by_name('detection_classes:0')
            # print("classes= "+str(classes))
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')
            # print("num_detections= "+str(num_detections))
            # print("4")
            
            (boxes, scores, classes, num_detections) = sess.run(
                [boxes, scores, classes, num_detections],
                feed_dict={image_tensor: image_np_expanded})
            # Visualization of the results of a detection.
            vis_util.visualize_boxes_and_labels_on_image_array(
                image_np,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index,
                use_normalized_coordinates=True,
                line_thickness=4)
            # # print("5")
            lst = np.squeeze(boxes)
            _boxes = lst[[x for x, i in enumerate(lst) if i.any()]] # remove np_array[0 0 0 0] from np.sqqueeze(boxes)
            # print("Boxes = " + str(_boxes))


            cv2.imshow('object detection', cv2.resize(image_np, (800, 600)))
            # print("6")
            # print("classes[] =" + str(classes) )
            with open('tvt.txt', 'w') as file:
                objects = []
                i = 1
                for index, value in enumerate(classes[0]):
                    i += 1
                    j = 0
                    if scores[0, index] > 0.5:
                        # print(category_index.get(value))
                        # print((category_index.get(value)).get('name'))
                        # object_dict[(category_index.get(value)).get('name')] = ''
                        # # prcess to get dimensions:
                        ymin = int(max(1,(_boxes[j][0] * imH)))
                        xmin = int(max(1,(_boxes[j][1] * imW)))
                        ymax = int(min(imH,(_boxes[j][2] * imH)))
                        xmax = int(min(imW,(_boxes[j][3] * imW)))
                        
                        if xmin <= imW / 3:
                            W_pos = "left "
                        elif xmin <= (imW / 3 * 2):
                            W_pos = "center "
                        else:
                            W_pos = "right "

                        if ymin <= imH / 3:
                            H_pos = "top "
                        elif ymin <= (imH / 3 * 2):
                            H_pos = "mid "
                        else:
                            H_pos = "bottom "
                        ##

                        objects.append(H_pos + W_pos + str((category_index.get(value)).get('name')))
                    print(objects) 
                print(objects,file=file)
                # print("value of iteration:" + str(i))

            if cv2.waitKey(25) & 0xFF == ord('w'):
                #close file
                #file.seek(0,0)
                # time.sleep(.25)
                with open('tvt.txt') as f:
                    lines = f.readlines()
                for i in range(len(lines)):
                    lines[i] = lines[i].replace("\n", "")

                engine.say(lines)
                engine.runAndWait()
                engine.stop()

            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break