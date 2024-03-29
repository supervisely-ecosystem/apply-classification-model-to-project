import supervisely as sly
from supervisely import logger
from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

from fastapi import Depends, HTTPException

import src.preferences.functions as card_functions

import src.preferences.widgets as card_widgets
import src.connect_to_model.widgets as connect_to_model_widgets
import src.select_input_projects.widgets as select_input_widgets

import src.sly_functions as f
import src.sly_globals as g


@card_widgets.select_preferences_button.add_route(app=g.app, route=card_widgets.select_preferences_button.Routes.BUTTON_CLICKED)
def select_preferences_button(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    try:
        if state['selectedLabelingMode'] == "Classes" and len(g.selected_classes_list) == 0:
            raise ValueError('classes not selected')

        # g.selected_classes_list = state['selectedClasses']  # till Umar fixing state replacing
        DataJson()['labelingDone'] = False
        DataJson()['labelingStarted'] = False

        card_widgets.preview_results_button.disabled = True
        DataJson()['current_step'] += 1
    except Exception as ex:
        logger.warn(f'Cannot select preferences: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot select preferences",
                                                     'message': f'{ex}'})
    finally:
        run_sync(DataJson().synchronize_changes())


@card_widgets.start_labeling_button.add_route(app=g.app, route=card_widgets.start_labeling_button.Routes.BUTTON_CLICKED)
def start_labeling_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    card_widgets.start_labeling_button.loading = True

    select_input_widgets.reselect_projects_button.disabled = True
    connect_to_model_widgets.reselect_model_button.disabled = True
    card_widgets.preview_results_button.disabled = True
    card_widgets.reselect_preferences_button.disabled = True

    DataJson()['labelingDone'] = False
    DataJson()['labelingStarted'] = True

    run_sync(DataJson().synchronize_changes())

    try:

        if state['selectedLabelingMode'] == "Classes" and len(g.selected_classes_list) == 0:
            raise ValueError('classes not selected')

        g.model_tag_suffix = ''
        g.updated_images_ids = set()

        card_functions.label_project(state=state)
        card_functions.upload_project()

        DataJson()['labelingDone'] = True
        sly.app.fastapi.shutdown()

    except Exception as ex:
        logger.warn(f'Cannot start labeling: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot start labeling",
                                                     'message': f'{ex}'})
    finally:
        DataJson()['labelingStarted'] = False

        select_input_widgets.reselect_projects_button.disabled = False
        connect_to_model_widgets.reselect_model_button.disabled = False
        card_widgets.preview_results_button.disabled = False
        card_widgets.reselect_preferences_button.disabled = False

        card_widgets.start_labeling_button.loading = False
        run_sync(DataJson().synchronize_changes())


@card_widgets.reselect_preferences_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_projects_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    DataJson()['current_step'] = 3
    card_widgets.preview_results_button.disabled = False
    run_sync(DataJson().synchronize_changes())


@card_widgets.preview_results_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def preview_results_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    card_widgets.preview_results_button.loading = True
    card_widgets.preview_grid_gallery.loading = True

    run_sync(DataJson().synchronize_changes())
    try:
        if state['selectedLabelingMode'] == "Classes" and len(g.selected_classes_list) == 0:
            raise ValueError('classes not selected')

        g.model_tag_suffix = ''
        g.updated_images_ids = set()

        images_for_preview = card_functions.get_images_for_preview(state=state, img_num=6)

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
    card_functions.selected_classes_event(state)


@card_widgets.select_all_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def select_all_classes_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    state["selectedClasses"] = [True] * len(g.available_classes_names)
    run_sync(state.synchronize_changes())
    card_functions.selected_classes_event(state)


@card_widgets.deselect_all_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def deselect_all_classes_button_clicked(state: sly.app.StateJson = Depends(sly.app.StateJson.from_request)):
    state["selectedClasses"] = [False] * len(g.available_classes_names)
    run_sync(state.synchronize_changes())
    card_functions.selected_classes_event(state)
