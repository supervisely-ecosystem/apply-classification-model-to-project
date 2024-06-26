import functools
import os
import random
import time
from typing import Any, Dict
from requests.exceptions import RetryError

import cv2
import numpy as np

import src.sly_functions as f
import src.sly_globals as g
import supervisely as sly
from supervisely.app import DataJson, StateJson
from supervisely.nn.inference.session import AsyncInferenceIterator, SessionJSON

import src.preferences.widgets as card_widgets


def get_classes_table_content(project_dir):
    table_data = []

    class2stats = f.get_classes_stats_for_project(project_dir)
    class2color = f.get_class2color_from_meta(project_dir)
    class2shape = f.get_class2shape_from_meta(project_dir)

    g.available_classes_names = []
    g.selected_classes_list = []

    for class_name in class2stats.keys():
        if class2shape[class_name] in [sly.Bitmap.geometry_name(),
                                       sly.Rectangle.geometry_name(),
                                       sly.Polygon.geometry_name()]:
            table_data.append({
                'name': class_name,
                'color': class2color[class_name],
                'shape': class2shape[class_name],
                **class2stats[class_name]
            })

            g.available_classes_names.append(class_name)

    return table_data


def get_objects_num_by_classes(selected_classes):
    total = 0
    for row in DataJson()['classes_table_content']:
        if row['name'] in selected_classes:
            total += row['obj_num']
    return total


def get_data_to_inference(images_batch):
    data = {
        'images_ids': [],
        'rectangles': []
    }

    for row in images_batch:

        if len(row) == 2:  # labels
            image_info, label = row

            label_bbox = label.geometry.to_bbox()
            bbox = [
                label_bbox.top,
                label_bbox.left,
                label_bbox.bottom,
                label_bbox.right
            ]

            data['rectangles'].append(bbox)

        else:  # only images
            image_info = row

        data['images_ids'].append(image_info.id)

    if len(data['rectangles']) == 0:  # remove rectangles if doesn't exist
        data.pop('rectangles')

    return data


def get_tags_list_for_predictions(predictions_row):

    pred_scores_list, pred_classes_list = predictions_row['score'], predictions_row['class']

    tags_list = []
    for name, value in zip(pred_classes_list, pred_scores_list):
        tag_meta = g.output_project_meta.get_tag_meta(f'{name}{g.model_tag_suffix}')

        if tag_meta.value_type == sly.TagValueType.NONE:
            tags_list.append(sly.Tag(meta=tag_meta))
        else:
            class_info = [class_info for class_info in StateJson()['modelClasses'] if class_info['name'] == name][0]
            if StateJson()['usePerClassThresholds'] and (value < float(class_info["confFrom"]) or value > float(class_info["confTo"])):
                continue
            tags_list.append(sly.Tag(meta=tag_meta, value=value))

    return tags_list


def add_predicted_tags_to_labels(labels_batch, predictions):
    updated_labels = []

    for index, row in enumerate(labels_batch):
        label: sly.Label = row[1]

        if predictions[index] is None:
            sly.logger.warning(f'cannot read prediction for label {row}')
            continue

        tags_list = get_tags_list_for_predictions(predictions[index])

        updated_labels.append(label.clone(tags=sly.TagCollection(tags_list)))

    return updated_labels


def get_predicted_tags_for_images(labels_batch, predictions):
    predicted_tags_collections = []

    for index, row in enumerate(labels_batch):

        if predictions[index] is None:
            sly.logger.warning(f'cannot read prediction for label {row}')
            continue

        tags_list = get_tags_list_for_predictions(predictions[index])
        predicted_tags_collections.append(sly.TagCollection(tags_list))

    return predicted_tags_collections


class InferenceSession(SessionJSON):
    def __init__(self, api: sly.Api, task_id: int):
        super().__init__(api, task_id)
    
    def _get_from_endpoint(self, endpoint) -> Dict[str, Any]:
        json_body = self._get_default_json_body()
        resp = self.api.task.send_request(self._task_id, endpoint, json_body["state"])
        return resp
    
    def _get_from_endpoint_for_async_inference(self, endpoint) -> Dict[str, Any]:
        json_body = self._get_default_json_body_for_async_inference()
        resp = self.api.task.send_request(self._task_id, endpoint, json_body["state"])
        return resp
    
    def _get_inference_result(self):
        json_body = self._get_default_json_body_for_async_inference()
        resp = self.api.task.send_request(self._task_id, "get_inference_result", json_body["state"])
        return resp
    
    def _pop_pending_results(self) -> Dict[str, Any]:
        endpoint = "pop_async_inference_results"
        return self._get_from_endpoint_for_async_inference(endpoint)

    def inference_batch_ids_async(self, inference_settings: Dict, logger=None, process_fn=None):
        if logger is None:
            logger = sly.logger
        if self._async_inference_uuid:
            logger.info(
                "Trying to run a new inference while `_async_inference_uuid` already exists. Stopping the old one..."
            )
            try:
                self.stop_async_inference()
                self._on_async_inference_end()
            except Exception as exc:
                logger.error(f"An error has occurred while stopping the previous inference. {exc}")
        endpoint = "inference_batch_ids_async"

        state = {}
        state.update(inference_settings)
        resp = self.api.task.send_request(self._task_id, endpoint, state)
        # resp = self._post(url, json=json_body).json()
        self._async_inference_uuid = resp["inference_request_uuid"]
        self._stop_async_inference_flag = False

        resp, has_started = self._wait_for_async_inference_start()
        logger.info("Inference has started:", extra={"response": resp})
        frame_iterator = AsyncInferenceIterator(
            resp["progress"]["total"], self, process_fn=process_fn
        )
        return frame_iterator



def get_predicted_labels_for_batch(labels_batch, model_session_id, top_n, padding, progress_cb=None):
    inference_data = get_data_to_inference(labels_batch)

    predictions = g.api1.task.send_request(model_session_id, "inference_batch_ids", data={
        'topn': top_n,
        'pad': padding,
        **inference_data
    })

    if len(labels_batch[0]) == 2:  # labels
        return add_predicted_tags_to_labels(labels_batch, predictions)
    else:  # images
        return get_predicted_tags_for_images(labels_batch, predictions)


def update_project_items_by_predicted_labels(labels_batch, predicted_labels):
    dsid2dataset = f.get_datasets_dict_by_project_dir(g.output_project_dir)

    for index, predicted_label in enumerate(predicted_labels):

        if len(labels_batch[index]) == 2:  # labels
            item_info, _ = labels_batch[index]
            dataset: sly.Dataset = dsid2dataset[item_info.dataset_id]

            if item_info.id in g.updated_images_ids:
                ann = dataset.get_ann(item_info.name, project_meta=g.output_project.meta)
            else:
                ann = sly.Annotation(img_size=(item_info.height, item_info.width))

            ann_labels = ann.labels
            ann_labels.append(predicted_label)
            updated_ann = ann.clone(labels=ann_labels)

        else:  # images
            item_info = labels_batch[index]
            dataset: sly.Dataset = dsid2dataset[item_info.dataset_id]

            updated_ann = sly.Annotation(img_size=(item_info.height, item_info.width), img_tags=predicted_label)

        dataset.set_ann(item_name=item_info.name, ann=updated_ann)

        if item_info.id not in g.updated_images_ids:
            g.updated_images_ids.add(item_info.id)


def update_annotations_in_for_loop(state):
    selected_classes_list = g.selected_classes_list if state['selectedLabelingMode'] == "Classes" else None
    total = get_objects_num_by_classes(selected_classes_list) if state['selectedLabelingMode'] == "Classes" else g.output_project.total_items

    topN = state["topN"]
    if state["cls_mode"] == "multi_label":
        topN = None
    padding = state['padding']
    model_session_id = state['model_id']

    labels = list(f.get_images_to_label(g.project_dir, selected_classes_list))
    try:
        with card_widgets.labeling_progress(message='classifying data', total=total) as pbar:
            inference_data = get_data_to_inference(labels)
            session = InferenceSession(g.api1, model_session_id)
            labels_batch = []
            predictions = []
            for i, prediction in enumerate(session.inference_batch_ids_async({**inference_data, 'topn': topN, 'pad': padding})):
                labels_batch.append(labels[i])
                predictions.append(prediction)
                batch_size = g.batch_size_reduced or state["batchSize"]
                if len(predictions) == batch_size:
                    if len(labels_batch[0]) == 2:  # labels
                        predictions = add_predicted_tags_to_labels(labels_batch, predictions)
                    else:  # images
                        predictions = get_predicted_tags_for_images(labels_batch, predictions)

                    update_project_items_by_predicted_labels(labels_batch, predictions)
                    labels_batch = []
                    predictions = []
                    pbar.update(len(predictions))
            if len(predictions) != 0:
                if len(labels_batch[0]) == 2:  # labels
                    predictions = add_predicted_tags_to_labels(labels_batch, predictions)
                else:  # images
                    predictions = get_predicted_tags_for_images(labels_batch, predictions)

                update_project_items_by_predicted_labels(labels_batch, predictions)
                pbar.update(len(predictions))

    except Exception:
        sly.logger.warn("Unable to apply inderence with session, trying to apply inference in for loop.", exc_info=True)
        with card_widgets.labeling_progress(message='classifying data', total=total) as pbar:
            labels_batch = []
            for label_info_to_annotate in labels:
                labels_batch.append(label_info_to_annotate)
                pbar.update()

                batch_size = g.batch_size_reduced or state["batchSize"]
                if len(labels_batch) == batch_size:
                    predicted_labels = get_predicted_labels_for_batch(
                        labels_batch=labels_batch,
                        model_session_id=model_session_id,
                        top_n=topN,
                        padding=padding
                    )
                    update_project_items_by_predicted_labels(labels_batch, predicted_labels)
                    labels_batch = []

            if len(labels_batch) != 0:
                predicted_labels = get_predicted_labels_for_batch(
                    labels_batch=labels_batch,
                    model_session_id=state['model_id'],
                    top_n=topN,
                    padding=state['padding']
                )
                update_project_items_by_predicted_labels(labels_batch, predicted_labels)


def label_project(state):
    f.create_output_project(input_project_dir=g.project_dir, output_project_dir=g.output_project_dir)
    f.update_project_tags_by_model_meta(project_dir=g.output_project_dir, state=state)

    g.output_project = sly.Project(g.output_project_dir, mode=sly.OpenMode.READ)
    g.output_project_meta = sly.Project(g.output_project_dir, mode=sly.OpenMode.READ).meta

    done = False
    while not done:
        try:
            update_annotations_in_for_loop(state=state)
            done = True
        except RetryError as ex:
            # reducing batch_size (8, 4, 2, 1, 0)
            if g.batch_size_reduced is None:
                g.batch_size_reduced = 8
            else:
                g.batch_size_reduced = g.batch_size_reduced // 2
            sly.logger.warn(f"Reducing batch_size to {g.batch_size_reduced}")

            if g.batch_size_reduced <= 0:
                raise Exception(f"Can't reduce batch_size further, retry limit exceeded.")


def upload_project():
    output_project_name = f"NN_{g.api.project.get_info_by_id(g.project['project_id']).name}"

    with card_widgets.labeling_progress(message='uploading project', total=g.output_project.total_items * 2) as pbar:
        project_id, project_name = sly.upload_project(dir=g.output_project_dir, api=g.api,
                                                      project_name=output_project_name,
                                                      workspace_id=g.WORKSPACE_ID, progress_cb=pbar.update)

        project_info = g.api.project.get_info_by_id(project_id)
        DataJson()['outputProject'] = {
            'projectUrl': sly.Project.get_url(project_id),
            'id': project_info.id,
            'name': project_name,
            'img_url': project_info.reference_image_url,
        }


def stringify_label_tags(predicted_tags, cls_mode=None):
    final_message = ''

    for index, tag in enumerate(predicted_tags):
        value = ''
        if tag.value is not None:
            value = f":{round(tag.value, 3)}"
        if cls_mode is None or cls_mode == 'one_label':
            final_message += f'top@{index + 1} — '
        final_message += f'{tag.name}{value}<br>'

    return final_message


@functools.lru_cache(maxsize=10)
def get_image_by_id(image_id):
    return cv2.cvtColor(g.api.image.download_np(image_id), cv2.COLOR_BGR2RGB)


def get_bbox_with_padding(rectangle, pad_percent, img_size):
    top, left, bottom, right = rectangle
    height, width = img_size

    if pad_percent > 0:
        sly.logger.debug("before padding", extra={"top": top, "left": left, "right": right, "bottom": bottom})
        pad_lr = int((right - left) / 100 * pad_percent)
        pad_ud = int((bottom - top) / 100 * pad_percent)
        top = max(0, top - pad_ud)
        bottom = min(height - 1, bottom + pad_ud)
        left = max(0, left - pad_lr)
        right = min(width - 1, right + pad_lr)
        sly.logger.debug("after padding", extra={"top": top, "left": left, "right": right, "bottom": bottom})

    return [top, left, bottom, right]


def clean_up_preview_images_dir():
    preview_files_path = os.path.join('static', 'preview_images')

    static_files_dir = os.path.join(g.app_root_directory, preview_files_path)
    os.makedirs(static_files_dir, exist_ok=True)
    sly.fs.clean_dir(static_files_dir)


def get_cropped_image_url(label_b, state):
    img_info, label = label_b
    img_np = get_image_by_id(img_info.id)

    try:
        sly_rectangle = label.geometry.to_bbox()
        rectangle = [
            sly_rectangle.top,
            sly_rectangle.left,
            sly_rectangle.bottom,
            sly_rectangle.right
        ]

        top, left, bottom, right = get_bbox_with_padding(rectangle=rectangle, pad_percent=state['padding'],
                                                         img_size=img_np.shape[:2])

        rect = sly.Rectangle(top, left, bottom, right)
        cropping_rect = rect.crop(sly.Rectangle.from_size(img_np.shape[:2]))[0]
        img_np = sly.image.crop(img_np, cropping_rect)

    except Exception as ex:
        sly.logger.warning(f'Cannot crop image: {ex}')

    if np.prod(img_np.shape[:2]) > 1:
        preview_files_path = os.path.join('static', 'preview_images')
        static_files_dir = os.path.join(g.app_root_directory, preview_files_path)

        filename = f'{img_info.id}_{time.time_ns()}.png'
        image_path = os.path.join(static_files_dir, filename)
        cv2.imwrite(image_path, img_np)

        return os.path.join(preview_files_path, filename)


def get_images_for_preview(state, img_num):
    clean_up_preview_images_dir()

    g.output_project_meta = f.get_project_meta_merged_with_model_tags(g.project_dir, state)

    selected_classes_list = g.selected_classes_list if state['selectedLabelingMode'] == "Classes" else None
    labels_batch = []
    for label_info_to_annotate in f.get_images_to_label(g.project_dir, selected_classes_list):
        labels_batch.append(label_info_to_annotate)
        if len(labels_batch) == img_num * 5:
            break

    random.shuffle(labels_batch)
    labels_batch = labels_batch[:img_num]
    topN = state["topN"]
    if state["cls_mode"] == "multi_label":
        topN = None
    predicted_labels = get_predicted_labels_for_batch(
        labels_batch=labels_batch,
        model_session_id=state['model_id'],
        top_n=topN,
        padding=state['padding']
    )

    images_for_preview = []
    for label_b, predicted_label in zip(labels_batch, predicted_labels):
        img_url = get_cropped_image_url(label_b, state) if len(label_b) == 2 else label_b.path_original
        if img_url is None:
            continue

        images_for_preview.append({
            'url': get_cropped_image_url(label_b, state) if len(label_b) == 2 else label_b.path_original,
            'title': stringify_label_tags(predicted_label.tags, state["cls_mode"]) if len(label_b) == 2 else stringify_label_tags(predicted_label, state["cls_mode"])
        })

    return images_for_preview


def selected_classes_event(state):
    g.selected_classes_list = []
    for idx, class_name in enumerate(g.available_classes_names):
        if state["selectedClasses"][idx] is True:
            g.selected_classes_list.append(class_name)
