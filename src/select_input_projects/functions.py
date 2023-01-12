import os
from datetime import time

import supervisely
from supervisely.app import StateJson, DataJson
from supervisely.app.widgets import ProjectSelector

import src.select_input_projects.widgets as card_widgets

import src.sly_functions as f
import src.sly_globals as g


def download_project(project_selector_widget: ProjectSelector, state: StateJson, project_dir):
    project_info = g.api.project.get_info_by_id(project_selector_widget.get_selected_project_id(state))
    pbar = card_widgets.download_projects_progress(message=f'downloading project', total=project_info.items_count)

    if os.path.exists(project_dir):
        supervisely.fs.clean_dir(project_dir)

    supervisely.download_project(g.api, project_info.id, project_dir, cache=None,
                                 progress_cb=pbar.update, save_image_info=True, save_images=False)

