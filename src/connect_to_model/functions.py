from urllib.parse import urlparse

import supervisely as sly
import src.sly_globals as g
from supervisely import logger


def validate_errors(data):
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


def connect_to_model(state):
    model_id = state['model_id']
    if model_id is None:
        raise ValueError('model_id must be a number')

    g.model_data['info'] = validate_errors(g.api.task.send_request(model_id, "get_session_info", data={}))
    g.model_data['model_meta'] = sly.ProjectMeta.from_json(
        validate_errors(g.api.task.send_request(model_id, "get_model_meta", data={})))
    g.model_data['tags_examples'] = validate_errors(g.api.task.send_request(model_id, "get_tags_examples", data={}))


def get_class_color_from_meta(class_name):
    class_color = "#000000"

    try:
        rgb_color = tuple(g.model_data['model_meta'].tag_metas.get(class_name).color)
        class_color = '#%02x%02x%02x' % rgb_color
    except Exception as ex:
        logger.warning(f'cannot get color for class {class_name}:'
                       f'{ex}')

    return class_color


def get_resized_images(images_list, height):
    resized_images_urls = []
    for image_storage_url in images_list:
        parsed_link = urlparse(image_storage_url)
        resized_images_urls.append({'preview': f'{parsed_link.scheme}://{parsed_link.netloc}'
                                               f'/previews/q/ext:jpeg/resize:fill:0:{height}:0/q:0/plain{parsed_link.path}'})
    return resized_images_urls


def get_model_classes_list():
    model_classes_list = []
    for class_name, images_links in g.model_data.get('tags_examples', {}).items():
        class_color = get_class_color_from_meta(class_name)
        class_images = get_resized_images(images_list=images_links, height=200)

        model_classes_list.append({
            'name': class_name,
            'color': class_color,
            'images': class_images[:10]
        })

    return model_classes_list
