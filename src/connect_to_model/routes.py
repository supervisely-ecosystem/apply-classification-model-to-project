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

        DataJson()['model_connected'] = True
        DataJson()['current_step'] += 1
    except Exception as ex:
        DataJson()['model_connected'] = False
        logger.warn(f'Cannot download projects: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot connect to model",
                                                     'message': f'Please reselect model and try again'})
    finally:
        card_widgets.connect_model_button.loading = False
        run_sync(DataJson().synchronize_changes())


@card_widgets.reselect_model_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_projects_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    DataJson()['current_step'] = 2
    run_sync(DataJson().synchronize_changes())
