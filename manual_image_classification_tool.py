import json
import sys

from glob import glob
from os import getcwd
from os.path import exists

from PyQt5.Qt import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton)


class MainWindow(QWidget):
    """
    Purpose: An easy to use boolean gui to classify images to their suspected classification label
    Features: Classify image as correct by clicking the `Yes` button or by pressing 1 on the keyboard
              Classify image as incorrect by clicking the `No` button or by pressing 2 on the keyboard
              Undo the last image classification
              The Undo button is unlimited, meaning it removes the last classification from the file every time the
                Undo button is pressed
    Limitations: Does not use a database, so interpolation amongst humans is limited
    """
    def __init__(self):
        super().__init__()

        # remove_duplicate_images()

        self.image_directory = 'imgs/'
        self.human_image_classification__data_file = 'human_image_classification_data_file.json'

        self.image_files = glob(f'{self.image_directory}/**/*.png', recursive=True)
        self.remaining_images_counter = len(self.image_files)

        self.setWindowTitle('M.I.C.T')
        self.setGeometry(625, 250, 300, 450)
        self.setStyleSheet('background-color: black;')
        self.yes_button()
        self.no_button()
        self.number_of_images()
        self.remaining_images(remaining_images_counter=self.remaining_images_counter)

        self.image_and_classification_generator = self.get_image_paths_and_classification()

        # Get the first image
        self.get_next_image_and_classification()

    def number_of_images(self):
        number_of_images = str(len(self.image_files))
        self.number_of_images_label = QLabel(self)
        self.number_of_images_label.setText(f'Total Images: {number_of_images}')
        self.number_of_images_label.setStyleSheet('color: white;')
        self.number_of_images_label.setGeometry(128, 400, 150, 30)

    def remaining_images(self, remaining_images_counter):
        self.remaining_images_label = QLabel(self)
        self.remaining_images_label.setText(f'Remaining Classifications: {str(remaining_images_counter)}')
        self.remaining_images_label.setStyleSheet('color: white;')
        self.remaining_images_label.setGeometry(42, 425, 250, 30)
        self.remaining_images_label.show()

    def prevent_human_from_classifying_the_same_set(self, filepath):
        with open(self.human_image_classification__data_file, 'r') as reader:
            data = json.load(reader)

        for x in data:
            # Shouldn't use a try/except here as its kind of dirty / hacky, but this is a very simple program...
            try:
                if x['filepath'] == filepath:
                    return True
            except KeyError:
                continue

        return False

    def get_next_image_and_classification(self):
        while True:
            try:
                self.data = next(self.image_and_classification_generator)
            except StopIteration:
                self.image.setText('All of the images have been classified!')
                return
            self.filepath = self.data['filepath']
            if not self.prevent_human_from_classifying_the_same_set(filepath=self.filepath):
                break

        self.classification_name = self.data['classification_name']
        self.set_image(filepath=self.filepath)
        self.set_image_label(classification_name=self.classification_name)

    def get_image_paths_and_classification(self):
        list_of_image_classifications_and_absolute_paths = list()
        image_cwd = f'{getcwd()}/{self.image_directory}'
        for filepath in self.image_files:

            absolute_filepath = f'{image_cwd}{filepath.replace(self.image_directory, "")}'

            # print(absolute_filepath)
            # print(filepath)

            # Get the classification name
            classification_name = filepath.split('/')[1]

            my_dict = dict()
            my_dict['classification_name'] = classification_name
            my_dict['filepath'] = absolute_filepath
            list_of_image_classifications_and_absolute_paths.append(my_dict)

        for x in list_of_image_classifications_and_absolute_paths:
            yield x

    def set_image_label(self, classification_name):
        classification_name = classification_name.upper() + ' ?'
        self.image_label = QLabel(classification_name, self)
        self.image_label.setGeometry(120, 10, 200, 30)
        self.image_label.setText(classification_name)
        self.image_label.setStyleSheet('color: white;')
        self.image_label.show()

    def yes_button(self):
        self.yes_btn = QPushButton(self)
        self.yes_btn.setGeometry(50, 260, 95, 30)
        self.yes_btn.setText('Yes')
        self.yes_btn.setStyleSheet('background-color: green;')
        self.yes_btn.clicked.connect(self.keyboard_press_one_function)

    def no_button(self):
        self.no_btn = QPushButton(self)
        self.no_btn.setGeometry(155, 260, 95, 30)
        self.no_btn.setText('No')
        self.no_btn.setStyleSheet('background-color: red;')
        self.no_btn.clicked.connect(self.keyboard_press_two_function)

    def set_image(self, filepath):
        self.image = QLabel(self)
        self.image.setGeometry(50, 50, 200, 200)
        pixmap = QPixmap(filepath).scaled(200, 200)
        self.image.setPixmap(pixmap)
        self.image.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_1:
            self.keyboard_press_one_function()
        elif event.key() == Qt.Key_2:
            self.keyboard_press_two_function()

    def update_image_classification_file(self, human_answer):
        if exists(self.human_image_classification__data_file):
            with open(self.human_image_classification__data_file, 'r') as reader:
                data = json.load(reader)
        else:
            data = []
            with open(self.human_image_classification__data_file, 'w') as writer:
                json.dump(data, writer, indent=4)

        my_dict = dict()
        my_dict['image_classification'] = self.data['classification_name']
        my_dict['human_answer'] = human_answer
        my_dict['image_filepath'] = self.data['filepath']
        data.append(my_dict)

        with open(self.human_image_classification__data_file, 'w') as writer:
            json.dump(data, writer, indent=4)

    def keyboard_press_one_function(self):
        # Save the new data to the disk
        self.update_image_classification_file(human_answer=True)

        # Get the next image
        self.get_next_image_and_classification()

        # De-increment the remaining image classification counter
        self.remaining_images_counter -= 1

        # Update the remaining image classification counter
        self.remaining_images(remaining_images_counter=self.remaining_images_counter)

        # print('You pressed 1 on the keyboard')

    def keyboard_press_two_function(self):
        # Save the new data to the disk
        self.update_image_classification_file(human_answer=False)

        # Get the next image
        self.get_next_image_and_classification()

        # print('You pressed 2 on the keyboard')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    demo = MainWindow()
    demo.show()

    sys.exit(app.exec_())