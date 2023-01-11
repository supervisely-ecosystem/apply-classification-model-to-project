from pathlib import Path

from jinja2 import Environment

from supervisely.app import StateJson, DataJson

import src.sly_globals as g

from src.preferences.routes import *
from src.preferences.functions import *
from src.preferences.widgets import *


StateJson()['selectedLabelingMode'] = "Classes"
StateJson()['outputProject'] = "New"
StateJson()['padding'] = 0
StateJson()['topN'] = 1
StateJson()['batchSize'] = 128
StateJson()['addConfidence'] = True
StateJson()['addSuffix'] = False
StateJson()['suffixValue'] = None

StateJson()['selectedClasses'] = []
DataJson()['classes_table_content'] = []


DataJson()['outputProject'] = {
    'id': None
}

DataJson()['labelingStarted'] = False
DataJson()['labelingDone'] = False




