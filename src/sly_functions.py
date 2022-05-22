import supervisely as sly


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

