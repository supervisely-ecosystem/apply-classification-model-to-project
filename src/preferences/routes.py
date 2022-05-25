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


@card_widgets.select_preferences_button.add_route(app=g.app, route=card_widgets.select_preferences_button.Routes.BUTTON_CLICKED)
def select_preferences_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    card_widgets.select_preferences_button.loading = True
    card_widgets.preview_results_button.disabled = True

    DataJson()['labelingDone'] = False
    DataJson()['labelingStarted'] = True

    run_sync(DataJson().synchronize_changes())

    try:
        if state['selectedLabelingMode'] == "Classes" and len(state['selectedClasses']) == 0:
            raise ValueError('classes not selected')

        g.model_tag_suffix = ''
        g.updated_images_ids = set()

        card_functions.label_project(state=state)
        card_functions.upload_project()

        DataJson()['labelingDone'] = True

    except Exception as ex:
        logger.warn(f'Cannot start labeling: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot start labeling",
                                                     'message': f'{ex}'})
    finally:
        DataJson()['labelingStarted'] = False

        card_widgets.preview_results_button.disabled = False
        card_widgets.select_preferences_button.loading = False
        run_sync(DataJson().synchronize_changes())


@card_widgets.reselect_preferences_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_projects_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    DataJson()['current_step'] = 3
    run_sync(DataJson().synchronize_changes())


@card_widgets.preview_results_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def preview_results_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    card_widgets.preview_results_button.loading = True
    card_widgets.preview_grid_gallery.loading = True

    run_sync(DataJson().synchronize_changes())
    try:
        if state['selectedLabelingMode'] == "Classes" and len(state['selectedClasses']) == 0:
            raise ValueError('classes not selected')

        g.model_tag_suffix = ''
        g.updated_images_ids = set()


        images_for_preview = card_functions.get_images_for_preview(state=state, img_num=9)

        card_widgets.preview_grid_gallery.clean_up()

        for current_image in images_for_preview:
            card_widgets.preview_grid_gallery.append(
                image_url=current_image['url'],
                title=current_image['title']
            )

    except Exception as ex:
        logger.warn(f'Cannot preview results: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot preview results",
                                                     'message': f'{ex}'})
    finally:
        card_widgets.preview_results_button.loading = False
        card_widgets.preview_grid_gallery.loading = False
        run_sync(DataJson().synchronize_changes())


@g.app.post('/classes_selection_change/')
def selected_classes_changed(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    pass
    # if len(state['selectedClasses']) > 0:
    #     card_widgets.select_preferences_button.disabled = False
    # else:
    #     card_widgets.select_preferences_button.disabled = True

    # run_sync(state.synchronize_changes())
    # run_sync(DataJson().synchronize_changes())


