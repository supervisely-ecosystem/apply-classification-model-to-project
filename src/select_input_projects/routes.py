import asyncio
import json
import time

from fastapi import Depends, HTTPException
from scipy.sparse import data
from starlette.responses import JSONResponse

import supervisely
from supervisely import logger

import src.select_input_projects.widgets as card_widgets
import src.select_input_projects.functions as card_functions

from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g
import src.sly_functions as f


@card_widgets.download_projects_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_projects(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.download_projects_button.loading = True
    card_widgets.project_selector.disabled = True

    run_sync(DataJson().synchronize_changes())

    try:
        card_functions.download_project(project_selector_widget=card_widgets.project_selector,
                                        state=state, project_dir=g.project_dir)


        g.project['workspace_id'] = card_widgets.project_selector.get_selected_workspace_id(state)
        g.project['project_id'] = card_widgets.project_selector.get_selected_project_id(state)


        card_widgets.projects_downloaded_done_label.text = 'project downloaded'

        DataJson()['current_step'] += 1
    except Exception as ex:
        card_widgets.project_selector.disabled = False

        logger.warn(f'Cannot download projects: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot download projects",
                                                     'message': f'Please reselect input data and try again'})

    finally:
        card_widgets.download_projects_button.loading = False
        run_sync(DataJson().synchronize_changes())


@card_widgets.reselect_projects_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_projects_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.project_selector.disabled = False

    DataJson()['current_step'] = 1
    run_sync(DataJson().synchronize_changes())
