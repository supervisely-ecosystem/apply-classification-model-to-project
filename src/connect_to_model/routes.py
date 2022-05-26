import asyncio
import json
import time

from fastapi import Depends, HTTPException
from scipy.sparse import data
from starlette.responses import JSONResponse

import supervisely
from supervisely import logger

import src.connect_to_model.widgets as card_widgets
import src.connect_to_model.functions as card_functions

import src.preferences.functions as preferences_functions
import src.preferences.widgets as preferences_widgets

from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g
import src.sly_functions as f


@card_widgets.connect_model_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def connect_to_model(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.connect_model_button.loading = True
    run_sync(DataJson().synchronize_changes())

    try:
        card_functions.connect_to_model(state)

        DataJson()['modelClasses'] = card_functions.get_model_classes_list()
        DataJson()['model_info'] = g.model_data.get('info')

        DataJson()['classes_table_content'] = preferences_functions.get_classes_table_content(g.project_dir)

        DataJson()['model_connected'] = True
        preferences_widgets.preview_results_button.disabled = False

        DataJson()['current_step'] += 1
    except Exception as ex:
        DataJson()['model_connected'] = False
        logger.warn(f'Cannot connect to model: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot connect to model",
                                                     'message': f'Please reselect model and try again'})
    finally:
        DataJson()['labelingDone'] = False

        card_widgets.connect_model_button.loading = False
        run_sync(DataJson().synchronize_changes())


@card_widgets.reselect_model_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_projects_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    DataJson()['current_step'] = 2
    DataJson()['model_connected'] = False
    preferences_widgets.preview_results_button.disabled = True
    run_sync(DataJson().synchronize_changes())


@g.app.post('/toggle_all_classes/')
def toggle_all_classes(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    if DataJson()['all_classes_collapsed'] is True:
        # card_widgets.toggle_all_previews_button.text = 'hide all'
        state['activeNames'] = [class_info['name'] for class_info in DataJson()['modelClasses']]
    else:
        # card_widgets.toggle_all_previews_button.text = 'show all'
        state['activeNames'] = []

    DataJson()['all_classes_collapsed'] = not DataJson()['all_classes_collapsed']
    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())
