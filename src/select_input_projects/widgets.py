import os

from supervisely.app import StateJson
from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel

import src.sly_globals as g

project_selector = ProjectSelector(team_id=g.TEAM_ID, workspace_id=g.WORKSPACE_ID,
                                   project_id=g.PROJECT_ID, team_is_selectable=False,
                                   datasets_is_selectable=False, widget_id="project_selector")

download_projects_button = ElementButton(text='DOWNLOAD', button_type='primary', widget_id="download_projects_button")
reselect_projects_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect',
                                         button_type='warning', button_size='small', plain=True, widget_id="reselect_projects_button")

download_projects_progress = SlyTqdm(message='', widget_id="download_projects_progress")

projects_downloaded_done_label = DoneLabel(widget_id="projects_downloaded_done_label")
