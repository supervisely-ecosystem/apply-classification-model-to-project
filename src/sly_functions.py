import os
import supervisely as sly

import src.sly_globals as g



def get_classes_names_from_meta(project_meta: sly.ProjectMeta):
    classes_names = []
    for obj_class in project_meta.obj_classes:
        classes_names.append(obj_class.name)
    return classes_names


def get_class2color_from_meta(project_dir):
    project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
    project_meta = project.meta

    class2color = {}
    for obj_class in project_meta.obj_classes:
        class2color[obj_class.name] = '#%02x%02x%02x' % tuple(obj_class.color)
    return class2color


def get_class2shape_from_meta(project_dir):
    project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
    project_meta = project.meta

    class2shape = {}
    for obj_class in project_meta.obj_classes:
        class2shape[obj_class.name] = obj_class.geometry_type.geometry_name()
    return class2shape


def get_classes_stats_for_project(project_dir) -> dict:
    project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
    project_meta = project.meta

    classes_names = get_classes_names_from_meta(project_meta=project_meta)

    classes_stats = {class_name: {'img_num': 0, 'obj_num': 0} for class_name in classes_names}

    for dataset in project.datasets:
        items_names = dataset.get_items_names()

        for item_name in items_names:
            annotation = dataset.get_ann(item_name=item_name, project_meta=project_meta)

            objects_num_on_item = {}

            for label in annotation.labels:
                objects_num_on_item[label.obj_class.name] = objects_num_on_item.get(label.obj_class.name, 0) + 1

            for obj_name, obj_num_on_item in objects_num_on_item.items():
                classes_stats[obj_name]['img_num'] += 1
                classes_stats[obj_name]['obj_num'] += obj_num_on_item

    return classes_stats


def get_images_to_label(project_dir, selected_classes_names=None) -> dict:
    project = sly.Project(directory=project_dir, mode=sly.OpenMode.READ)
    project_meta = project.meta

    for dataset in project.datasets:
        items_names = dataset.get_items_names()

        for item_name in items_names:
            annotation = dataset.get_ann(item_name=item_name, project_meta=project_meta)
            image_info = dataset.get_image_info(item_name=item_name)

            if selected_classes_names is not None:
                for label in annotation.labels:
                    if label.obj_class.name in selected_classes_names:
                        yield tuple([image_info, label])
            else:
                yield image_info


def create_output_project(input_project_dir, output_project_dir):
    os.makedirs(output_project_dir, exist_ok=True)
    sly.fs.clean_dir(output_project_dir)
    sly.Project(directory=input_project_dir, mode=sly.OpenMode.READ).copy_data(dst_directory=os.path.join(g.app_root_directory, 'tempfiles'), dst_name='output_project_dir')


def update_project_tags_by_model_meta(project_dir):
    model_meta: sly.ProjectMeta = g.model_data['model_meta']

    tags_metas_list = []
    for tag_meta in model_meta.tag_metas:
        tags_metas_list.append(sly.TagMeta(name=f'nn_{tag_meta.name}', value_type=sly.TagValueType.ANY_NUMBER))

    project = sly.Project(project_dir, mode=sly.OpenMode.READ)

    meta_with_model_labels = sly.ProjectMeta(tag_metas=sly.TagMetaCollection(tags_metas_list))
    meta_with_model_labels = project.meta.merge(meta_with_model_labels)
    project.set_meta(meta_with_model_labels)

    g.output_project = project


def get_datasets_dict_by_project_dir(directory):
    project = sly.Project(directory=directory, mode=sly.OpenMode.READ)
    dsid2dataset = {}
    for key, value in zip(project.datasets.keys(), project.datasets.items()):
        dsid2dataset[g.api.dataset.get_info_by_name(parent_id=g.project['project_id'], name=key).id] = value
    return dsid2dataset

