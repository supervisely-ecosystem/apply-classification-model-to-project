import src.sly_functions as f


def get_classes_table_content(project_dir):
    table_data = []

    class2stats = f.get_classes_stats_for_project(project_dir)
    class2color = f.get_class2color_from_meta(project_dir)
    class2shape = f.get_class2shape_from_meta(project_dir)

    for class_name in class2stats.keys():
        table_data.append({
            'name': class_name,
            'color': class2color[class_name],
            'shape': class2shape[class_name],
            **class2stats[class_name]
        })

    return table_data
