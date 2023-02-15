from pathlib import Path

from jinja2 import Environment

from supervisely.app import StateJson, DataJson

import src.sly_globals as g

from src.connect_to_model.routes import *
from src.connect_to_model.functions import *
from src.connect_to_model.widgets import *

DataJson()["model_options"] = {
        "sessionTags": ["deployed_nn_cls"],
        # "sessionTags": None,
        "showLabel": False,
        "size": "small"
}

DataJson()['model_info'] = None


DataJson()['model_connected'] = False
StateJson()['model_id'] = None

DataJson()['modelClasses'] = None
DataJson()['all_classes_collapsed'] = True

StateJson()['activeNames'] = []
StateJson()['cls_mode'] = 'one_label'
StateJson()['confThresh'] = []





