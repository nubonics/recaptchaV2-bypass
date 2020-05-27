<<<<<<< HEAD
=======



>>>>>>> 3e5733e756b03bf17c31a181957fc0792e9dde14
from time import sleep
import requests
from selenium import webdriver
from PIL import Image
import random
import string
import cv2
import os
import pathlib

import numpy as np
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession

from selenium.webdriver.firefox.options import Options

#http://download.tensorflow.org/models/object_detection/mask_rcnn_inception_v2_coco_2018_01_28.tar.gz

class RecaptchaElement(object):
    """docstring for RecaptchaElement"""
    def __init__(self, element, row, col, img, type):
        super(RecaptchaElement, self).__init__()
        self.row = row
        self.column = col
        self.element = element
        self.img = img
        self.type = type
                
    def click(self):
        self.element.click()

    def render_img(self):
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(self.img)
        img.show()

class TFRecaptcha(object):
    """docstring for TFRecaptcha"""
    def __init__(self):
        super(TFRecaptcha, self).__init__()
        self.test_url = "https://patrickhlauke.github.io/recaptcha/"
        self.recaptcha_types = [
            'fire hydrant',
            'fire hydrants',
            'bicycle',
            'bicycles',
            'traffic light',
            'traffic lights',
            'bus',            
            'buses',         
            'taxis',
            'cars',
            'motorcycle',
            'motorcycles',
            'crosswalk',
            'crosswalks'
        ]
        """
        The individual recaptcha image elements will be saved in
        the same row/column order that the HTML elements are in
        """
        self.elements = []
        self.recaptchas = []
        #Bool for determining harvesting or solving mode
        self.harvest_mode = False
        self.model_name = 'mask_rcnn_inception_v2_coco_2018_01_28'
        self.create_image_class_dirs()

    def create_image_class_dirs(self):
        for type in self.recaptcha_types:
            try:
                os.mkdir("imgs/{0}/".format(type))
                os.mkdir("imgs/{0}/3x3/".format(type))
                os.mkdir("imgs/{0}/4x4/".format(type))
            except:
                print("[INFO] Skipping image class directory creation for {0}".format(type))

    def init_tf(self):
        # patch tf1 into `utils.ops`
        utils_ops.tf = tf.compat.v1
        tf.gfile = tf.io.gfile
        # fix for https://stackoverflow.com/questions/43147983/could-not-create-cudnn-handle-cudnn-status-internal-error
        config = ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = 0.6
        config.gpu_options.allow_growth = True
        session = InteractiveSession(config=config)
        self.detection_model = self.load_model(self.model_name)
        # List of the strings that is used to add correct label for each box.
        self.PATH_TO_LABELS = 'models/research/object_detection/data/mscoco_label_map.pbtxt'
        self.category_index = label_map_util.create_category_index_from_labelmap(self.PATH_TO_LABELS, use_display_name=True)
        # Patch the location of gfile


    def load_model(self, model_name):
      base_url = 'http://download.tensorflow.org/models/object_detection/'
      model_file = model_name + '.tar.gz'
      model_dir = tf.keras.utils.get_file(
        fname=model_name, 
        origin=base_url + model_file,
        untar=True)

      model_dir = pathlib.Path(model_dir)/"saved_model"
      #model = tf.compat.v2.saved_model.load(str(model_dir), None)
      model = tf.saved_model.load(str(model_dir))
      model = model.signatures['serving_default']

      return model

    def run_inference_for_single_image(self, model, image):
      #image = np.asarray(image)
      # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
      input_tensor = tf.convert_to_tensor(image)
      # The model expects a batch of images, so add an axis with `tf.newaxis`.
      input_tensor = input_tensor[tf.newaxis,...]

      # Run inference
      output_dict = model(input_tensor)

      # All outputs are batches tensors.
      # Convert to numpy arrays, and take index [0] to remove the batch dimension.
      # We're only interested in the first num_detections.
      num_detections = int(output_dict.pop('num_detections'))
      output_dict = {key:value[0, :num_detections].numpy() 
                     for key,value in output_dict.items()}
      output_dict['num_detections'] = num_detections

      # detection_classes should be ints.
      output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
       
      # Handle models with masks:
      if 'detection_masks' in output_dict:
        # Reframe the the bbox mask to the image size.
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                  output_dict['detection_masks'], output_dict['detection_boxes'],
                   image.shape[0], image.shape[1])      
        detection_masks_reframed = tf.cast(detection_masks_reframed > 0.5,
                                           tf.uint8)
        output_dict['detection_masks_reframed'] = detection_masks_reframed.numpy()
        
      return output_dict

    def run_inference(self, model, image_np):
      # the array based representation of the image will be used later in order to prepare the
      # result image with boxes and labels on it.
      #image_np = np.array(Image.open(image_path))
      # Actual detection.
      output_dict = self.run_inference_for_single_image(model, image_np)
      # Visualization of the results of a detection.
      vis_util.visualize_boxes_and_labels_on_image_array(
          image_np,
          output_dict['detection_boxes'],
          output_dict['detection_classes'],
          output_dict['detection_scores'],
          self.category_index,
          instance_masks=output_dict.get('detection_masks_reframed', None),
          use_normalized_coordinates=True,
          line_thickness=8)
      results = [self.category_index.get(value) for index,value in enumerate(output_dict['detection_classes']) if output_dict['detection_scores'][index] > 0.5]
      classes = {v['id']:v for v in results}.values()
      output = []
      for c in classes:
        output.append(c['name'])
      #print(image_path)
      print(output)
      return output


    """ Initalize the Firefox browser """
    def init_browser(self):

        # options = Options()
        # options.set_headless()
        # self.browser = webdriver.Firefox(options=options)
        self.browser = webdriver.Firefox()
        if self.browser:
            return True
        else:
            print("[ERROR] TFRecaptcha::init_browser(): Failed to create Firefox webdriver instance.")
            return False

    def detect_recaptcha_type(self, target_types=None):
        """
        This tries to get the text from the ReCaptcha element to determine what class of object is requested
        """
        try:
            raw = self.browser.page_source
            for captcha_type in self.recaptcha_types:
                if captcha_type in raw:
                    if target_types is None:
                        return True, captcha_type
                    else:
                        for target in target_types:
                            if target in raw:
                                return True, captcha_type
                        else:
                            return False, captcha_type
            return False, None
        except Exception as e:
            print("[ERROR] TFRecaptcha::detect_recaptcha_type()): {0}".format(e))
            return False, None
        return False, None

    def detect_incomplete_verify(self):
        """
        This is for detecting the verify button is clicked, but not all of the expected 
        puzzle elements have been clicked.
        """
        return bool(self.browser.find_element_by_class_name("rc-imageselect-error-select-more").text)
    
    def detect_failure_to_wait_for_img_refresh(self):
        return bool(self.browser.find_element_by_class_name("rc-imageselect-error-dynamic-more").text)
        
    def is_3x3_image_grid(self):
        """ 
        The recaptchas seem to either be 3x3 or 4x4 puzzles.
        The 3x3 is a single image but cut up into 3x3 grid
        The 4x4 is a single image with something to make it more like an overlay grid.
        """
        return bool(self.browser.find_elements_by_class_name("rc-image-tile-33"))

    def download_url(self, url, filename):
        """
        Used for downloading the images from URL
        """
        data = requests.get(url).content
        with open(filename, 'wb') as handler:
            handler.write(data)

    def download_recaptcha_img(self, type):
        """
        Used to detect what type of image and handle downloading it for processing
        """
        rand = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
        try:
            img_src = self.browser.find_element_by_class_name("rc-image-tile-44").get_attribute("src")
            grid_size = 4
        except:
            img_src = self.browser.find_element_by_class_name("rc-image-tile-33").get_attribute("src")
            grid_size = 3
        if img_src:
            if type:

                file_path = "imgs/{0}/{1}x{1}/{1}.png".format(type, grid_size, rand)
            else:
                file_path = "imgs/unknown/{0}x{0}/{1}.png".format(grid_size, rand)
            self.download_url(img_src, file_path)
            return file_path
        else:
            print("[ERROR] TFRecaptcha::download_recaptcha_img(): Failed to download recaptcha image.")

    def get_recaptcha_elements(self):
        """
        Gets a list of the individual recaptcha elements
        """
        self.elements = self.browser.find_elements_by_class_name("rc-image-tile-wrapper")
        
    def open_recaptcha(self):
        """
        This will handle the funny process of getting to the frame for interacting with the recaptcha
        This took hours to figure out
        """
        self.browser.get(self.test_url)
        sleep(2)
        self.browser.find_elements_by_xpath("//iframe[contains(@src, 'google')]")[0].click()
        sleep(2)
        #Sauce
        recaptcha_iframe = self.browser.find_element_by_xpath("//iframe[contains(@title, 'recaptcha challenge')]")
        self.browser.switch_to.frame(recaptcha_iframe)
        if not self.is_3x3_image_grid():
            print("[INFO] Attempting to bypass 4x4 puzzle type")
            self.attempt_puzzle_type_bypass()

    def detect_denial_of_service():
        return bool(self.browser.find_element_by_class_name("rc-doscaptcha-header"))
        
    def close_browser(self):
        self.browser.close()

    def click_solve_or_skip(self):
        self.browser.find_element_by_class_name("rc-button-default").click()

    def attempt_puzzle_type_bypass(self, retries=24):
        is_3x3 = self.is_3x3_image_grid()
        for i in range(1, retries):
            self.click_solve_or_skip()
            sleep(1)
            new_type = self.is_3x3_image_grid()
            if new_type == is_3x3:
                continue
            else:
                break

    def handle_incomplete_puzzle_result(self):
        pass

    def attempt_object_type_bypass(self, retries=24):
        ret, type = self.detect_recaptcha_type()
        if ret:
            for i in range(1, retries):
                self.click_solve_or_skip()
                sleep(1)
                new_type = self.detect_recaptcha_type()
                if type == new_type:
                    continue
                else:
                    print("[INFO] Detected new puzzle object type: {0}".format(new_type))
                    break

    def generate_recaptcha_classes(self):
        """
        This will try to turn the ReCaptcha elements into seperate RecaptchaElement classes
        """
        self.get_recaptcha_elements()
        ret, type = self.detect_recaptcha_type()
        if self.is_3x3_image_grid():
            grid_size = 3
        else:
            grid_size = 4
        saved_img = self.download_recaptcha_img(type)
        im =  cv2.imread(saved_img)
        imgheight=im.shape[0]
        imgwidth=im.shape[1]
        y1 = 0
        M = imgheight//grid_size
        N = imgwidth//grid_size
        index = -1
        for x in range(0, imgheight, N):
            for y in range(0, imgwidth, M):
                index += 1
                y1 = y + M
                x1 = x + N
                tile = im[x:x+N,y:y+M,]
                cv2.rectangle(im, (x, y), (x1, y1), (0, 0, 0))
                if self.harvest_mode:
                    rand = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
                    file_path = "imgs/{0}/{1}x{1}/{2}.png".format(type, grid_size, rand)
                    cv2.imwrite(file_path, tile)
                    print("Saved Img: {0}".format(file_path))
                r = RecaptchaElement(self.elements[index], x, y, tile, type)
                self.recaptchas.append(r) 


    def click_random_puzzle_element(self):
      pass

<<<<<<< HEAD
=======

>>>>>>> 3e5733e756b03bf17c31a181957fc0792e9dde14
#if __name__ == "__main__":
    # TFR = TFRecaptcha()
    # while True:
    #     TFR.recaptchas = []
    #     TFR.init_browser()
    #     #Harvest mode just skips the solving and only saves the puzzle images
    #     TFR.harvest_mode = True
    #     TFR.open_recaptcha()
    #     TFR.generate_recaptcha_classes()
    #     #Now each of the puzzle elements can be accessed through the RecaptchaElement class.
    #     for i in TFR.recaptchas:
    #         if i.type in run_inference(self.detection_model, i.img):
    #             i.click()
    #     sleep(1)
    #     TFR.click_solve_or_skip()
    #     print("Puzzle Type: {}".format(TFR.recaptchas[0].type))
    #     print("Incomplete Puzzle: {}".format(TFR.detect_incomplete_verify()))
    #     print("Failure To Wait For Image Refresh: {}".format(TFR.detect_failure_to_wait_for_img_refresh()))
    #     TFR.detect_failure_to_wait_for_img_refresh()
    #     sleep(1)
    #     TFR.close_browser()
