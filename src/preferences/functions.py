import src.sly_functions as f
import src.sly_globals as g
import supervisely as sly
from supervisely.app import DataJson

import src.preferences.widgets as card_widgets


def get_classes_table_content(project_dir):
    table_data = []

    class2stats = f.get_classes_stats_for_project(project_dir)
    class2color = f.get_class2color_from_meta(project_dir)
    class2shape = f.get_class2shape_from_meta(project_dir)

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


def add_predicted_tags_to_labels(labels_batch, predictions):
    updated_labels = []

    for index, row in enumerate(labels_batch):
        label: sly.Label = row[1]

        pred_scores_list, pred_classes_list = predictions[index]['score'], predictions[index]['class']

        tags_list = []
        for name, value in zip(pred_classes_list, pred_scores_list):
            tag_meta = g.output_project.meta.get_tag_meta(f'{name}{g.model_tag_suffix}')

            if tag_meta.value_type == sly.TagValueType.NONE:
                tags_list.append(sly.Tag(meta=tag_meta))
            else:
                tags_list.append(sly.Tag(meta=tag_meta, value=value))

        updated_labels.append(label.clone(tags=sly.TagCollection(tags_list)))

    return updated_labels


def get_predicted_tags_for_images(labels_batch, predictions):
    predicted_tags_collections = []

    for index, row in enumerate(labels_batch):
        pred_scores_list, pred_classes_list = predictions[index]['score'], predictions[index]['class']

        tags_list = []
        for name, value in zip(pred_classes_list, pred_scores_list):
            tag_meta = g.output_project.meta.get_tag_meta(f'{name}{g.model_tag_suffix}')

            if tag_meta.value_type == sly.TagValueType.NONE:
                tags_list.append(sly.Tag(meta=tag_meta))
            else:
                tags_list.append(sly.Tag(meta=tag_meta, value=value))

        predicted_tags_collections.append(sly.TagCollection(tags_list))

    return predicted_tags_collections


def get_predicted_labels_for_batch(labels_batch, model_session_id, top_n, padding):
    inference_data = get_data_to_inference(labels_batch)
    predictions = g.api.task.send_request(model_session_id, "inference_batch_ids", data={
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
    selected_classes_list = state['selectedClasses'] if state['selectedLabelingMode'] == "Classes" else None
    total = get_objects_num_by_classes(selected_classes_list) if state['selectedLabelingMode'] == "Classes" else g.output_project.total_items

    with card_widgets.labeling_progress(message='classifying data', total=total) as pbar:
        labels_batch = []

        for label_info_to_annotate in f.get_images_to_label(g.project_dir, selected_classes_list):
            labels_batch.append(label_info_to_annotate)
            pbar.update()

            if len(labels_batch) == g.batch_size:
                predicted_labels = get_predicted_labels_for_batch(
                    labels_batch=labels_batch,
                    model_session_id=state['model_id'],
                    top_n=state['topN'],
                    padding=state['padding']
                )
                update_project_items_by_predicted_labels(labels_batch, predicted_labels)
                labels_batch = []

        if len(labels_batch) != 0:
            predicted_labels = get_predicted_labels_for_batch(
                labels_batch=labels_batch,
                model_session_id=state['model_id'],
                top_n=state['topN'],
                padding=state['padding']
            )
            update_project_items_by_predicted_labels(labels_batch, predicted_labels)


def label_project(state):
    f.create_output_project(input_project_dir=g.project_dir, output_project_dir=g.output_project_dir)
    f.update_project_tags_by_model_meta(project_dir=g.output_project_dir, state=state)
    update_annotations_in_for_loop(state=state)


def upload_project():
    output_project_name = f"NN_{g.api.project.get_info_by_id(g.project['project_id']).name}"

    with card_widgets.labeling_progress(message='uploading project', total=g.output_project.total_items * 2) as pbar:
        project_id, project_name = sly.upload_project(dir=g.output_project_dir, api=g.api,
                                                      project_name=output_project_name,
                                                      workspace_id=g.WORKSPACE_ID, progress_cb=pbar.update)

        project_info = g.api.project.get_info_by_id(project_id)
        DataJson()['outputProject'] = {
            'id': project_info.id,
            'name': project_name,
            'img_url': project_info.reference_image_url,
        }