
import os
import xml.etree.ElementTree as ET
import logging
import json
from utils import extract_tar


class DokkiBuilder():
    ROOT_DIR_NAME = "output"

    def __init__(self, dataset_tar:str, output_dir:str):
        self.source_jar_dir = os.path.dirname(dataset_tar)
        self.extracted_jar_dir = output_dir
        self.dataset_dir = os.path.join(output_dir, DokkiBuilder.ROOT_DIR_NAME)
        if not self.__tar_already_extracted():
            logging.info("Dataset %s not extracted yet. Extracting at %s",self.dataset_dir, output_dir)
            extract_tar(dataset_tar, output_dir)
        self.__config_labels()


    def build(self):
        images_ids = self.__load_images_ids()
        train_images, train_objects = self.__load_bboxes_and_labels(images_ids)
        print(train_images)
        self.__save_images_and_objets_description_json(train_images, train_objects)


    def __config_labels(self):
        self.label_map={}
        self.label_map['background'] = 0
        self.label_map['total'] = 1


    def __load_images_ids(self):
        imgs_dir = os.path.join(self.extracted_jar_dir, DokkiBuilder.ROOT_DIR_NAME)
        all_files = os.listdir(imgs_dir)
        logging.info("Total of %d images id loaded.",len(all_files))
        return all_files

    def __tar_already_extracted(self) -> bool:
        return os.path.exists(self.dataset_dir)


    def __load_bboxes_and_labels(self, images_ids):
        train_images = list()
        train_objects = list()
        n_objects = 0
        for image_id in images_ids:
            objects = self.__parse_annotation_xml(image_id)
            n_objects += len(objects)
            train_objects.append(objects)
            absolute_image_path = os.path.join(self.dataset_dir, image_id )
            train_images.append(absolute_image_path)
        assert len(train_objects) == len(train_images)
        logging.info('There are %d training images containing a total of %d objects.',len(train_images), n_objects)
        return train_images, train_objects

    def __save_images_and_objets_description_json(self, train_images, train_objects):
        json_files =  [ os.path.join(self.extracted_jar_dir,f) for f in ['TRAIN_images.json', 'TRAIN_objects.json', 'label_map.json']]
        json_lists = [train_images, train_objects, self.label_map]
        self.__clean_up_json_files(json_files)
        for i, file in enumerate(json_files):
            logging.info("Generating %s", file)
            with open(file, 'w') as j:
                json.dump(json_lists[i], j)

    def __clean_up_json_files(self, files: list):
        for f in files:
            if os.path.exists(f):
                logging.info("Apagando %s",f)
                os.remove(f)

    def __parse_annotation_xml(self, id:str):

        boxes = list()
        labels = list()
        difficulties = list()
        difficult = 0


        xmin = 202
        ymin = 1496
        xmax = 1576
        ymax = 1560

        boxes.append([xmin, ymin, xmax, ymax])
        print(self.label_map)
        labels.append(self.label_map['total'])
        difficulties.append(difficult)

        return {'boxes': boxes, 'labels': labels, 'difficulties': difficulties}

class VOCJsonBuilder():
    """Processa o jar PascalVOC especificado e gera um JSON listando o caminho absoluto das imagens e um json com os bboxes, labels e difficulties"""

    VOC_ROOT_DIR_NAME = "VOCdevkit"
    VOC_TRAIN_VAL_FILE = "ImageSets/Main/trainval.txt"

    def __init__(self, voc_tar:str, output_dir:str):
        year =  self.__extract_year_from_jar_path(voc_tar)
        self.source_jar_dir = os.path.dirname(voc_tar)
        self.extracted_jar_dir = output_dir
        self.dataset_dir = os.path.join(output_dir, VOCJsonBuilder.VOC_ROOT_DIR_NAME, "VOC" + year)
        if not self.__tar_already_extracted():
            logging.info("VOC %s not extracted yet. Extracting at %s",self.dataset_dir, output_dir)
            extract_tar(voc_tar, output_dir)
        self.__config_labels()

    def __extract_year_from_jar_path(self, path):
        return path[-8: -4]

    def build(self):
        images_ids = self.__load_images_ids()
        train_images, train_objects = self.__load_bboxes_and_labels(images_ids)
        self.__save_images_and_objets_description_json(train_images, train_objects)


    def __config_labels(self):
        voc_labels = ('aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable',
              'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor')
        self.label_map = {k: v + 1 for v, k in enumerate(voc_labels)}
        self.label_map['background'] = 0


    def __load_images_ids(self):
        imageset_xml_path = os.path.join(self.dataset_dir, VOCJsonBuilder.VOC_TRAIN_VAL_FILE)
        logging.info("Loading images id from %s.",imageset_xml_path)
        with open(imageset_xml_path) as f:
            ids = f.read().splitlines()
        logging.info("Total of %d images id loaded.",len(ids))
        return ids

    def __tar_already_extracted(self) -> bool:
        return os.path.exists(self.dataset_dir)


    def __load_bboxes_and_labels(self, images_ids):
        train_images = list()
        train_objects = list()
        n_objects = 0
        for image_id in images_ids:
            objects = self.__parse_annotation_xml(image_id)
            if len(objects['boxes']) == 0:
                continue
            n_objects += len(objects)
            train_objects.append(objects)
            absolute_image_path = os.path.join(self.dataset_dir, 'JPEGImages', image_id + '.jpg')
            train_images.append(absolute_image_path)
        assert len(train_objects) == len(train_images)
        logging.info('There are %d training images containing a total of %d objects.',len(train_images), n_objects)
        return train_images, train_objects

    def __save_images_and_objets_description_json(self, train_images, train_objects):
        json_files =  [ os.path.join(self.extracted_jar_dir,f) for f in ['TRAIN_images.json', 'TRAIN_objects.json', 'label_map.json']]
        json_lists = [train_images, train_objects, self.label_map]
        self.__clean_up_json_files(json_files)
        for i, file in enumerate(json_files):
            logging.info("Generating %s", file)
            with open(file, 'w') as j:
                json.dump(json_lists[i], j)

    def __clean_up_json_files(self, files: list):
        for f in files:
            if os.path.exists(f):
                logging.info("Apagando %s",f)
                os.remove(f)

    def __parse_annotation_xml(self, id:str):

        annotation_path = os.path.join(self.dataset_dir, 'Annotations', id + '.xml')
        tree = ET.parse(annotation_path)
        root = tree.getroot()

        boxes = list()
        labels = list()
        difficulties = list()
        for object in root.iter('object'):

            difficult = int(object.find('difficult').text == '1')

            label = object.find('name').text.lower().strip()
            if label not in self.label_map:
                continue

            bbox = object.find('bndbox')
            xmin = int(bbox.find('xmin').text) - 1
            ymin = int(bbox.find('ymin').text) - 1
            xmax = int(bbox.find('xmax').text) - 1
            ymax = int(bbox.find('ymax').text) - 1

            boxes.append([xmin, ymin, xmax, ymax])
            labels.append(self.label_map[label])
            difficulties.append(difficult)

        return {'boxes': boxes, 'labels': labels, 'difficulties': difficulties}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    #descriptor = VOCJsonBuilder('/home/gugaime/Documentos/Datasets/VOCtrainval_06-Nov-2007.tar',"/tmp/VOC")
    descriptor = DokkiBuilder('/tmp/notafiscalpaulista.tar.xz',"/tmp/notafiscalpaulista")
    descriptor.build()
