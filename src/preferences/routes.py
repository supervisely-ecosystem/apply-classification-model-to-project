import supervisely as sly
from supervisely import logger
from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

from fastapi import Depends, HTTPException

import src.preferences.functions as card_functions

import src.preferences.widgets as card_widgets

import src.sly_functions as f
import src.sly_globals as g


@card_widgets.select_preferences_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def select_preferences_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):

    card_widgets.select_preferences_button.loading = True
    DataJson()['labelingDone'] = False

    run_sync(DataJson().synchronize_changes())

    try:
        if state['selectedLabelingMode'] == "Classes" and len(state['selectedClasses']) == 0:
            raise ValueError('classes not selected')

        g.updated_images_ids = set()

        card_functions.label_project(state=state)

        with card_widgets.labeling_progress(message='uploading project', total=g.output_project.total_items * 2) as pbar:
            project_id, _ = sly.upload_project(dir=g.output_project_dir, api=g.api, project_name=g.output_project.name,
                                               workspace_id=g.WORKSPACE_ID, progress_cb=pbar.update)

            project_info = g.api.project.get_info_by_id(project_id)
            DataJson()['outputProject'] = {
                'id': project_info.id,
                'name': f"NN_{g.api.project.get_info_by_id(g.project['project_id']).name}",
                'img_url': project_info.reference_image_url,
            }
        DataJson()['labelingDone'] = True

    except Exception as ex:

        logger.warn(f'Cannot start labeling: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot start labeling",
                                                     'message': f'{ex}'})
    finally:
        card_widgets.select_preferences_button.loading = False
        run_sync(DataJson().synchronize_changes())


@card_widgets.reselect_preferences_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_projects_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    DataJson()['current_step'] = 3
    run_sync(DataJson().synchronize_changes())

