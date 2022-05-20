import supervisely as sly
import src.sly_globals as g


def validate_errors(data):
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


def connect_to_model(state):
    model_id = state['model_id']
    if model_id is None:
        raise ValueError('model_id must be a number')

    g.model_data['info'] = validate_errors(g.api.task.send_request(model_id, "get_session_info", data={}))
    g.model_data['meta_json'] = sly.ProjectMeta.from_json(validate_errors(g.api.task.send_request(model_id, "get_model_meta", data={})))
    g.model_data['tags_examples'] = validate_errors(g.api.task.send_request(model_id, "get_tags_examples", data={}))
