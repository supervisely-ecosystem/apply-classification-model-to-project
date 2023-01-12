import os
from pathlib import Path

from fastapi import FastAPI

from supervisely import FileCache
from supervisely.app import DataJson
from supervisely.sly_logger import logger
from starlette.staticfiles import StaticFiles

import supervisely as sly
from supervisely.app.fastapi import create, Jinja2Templates

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")

api: sly.Api = sly.Api.from_env()
app = FastAPI()
sly_app = create()

TEAM_ID = int(os.getenv('context.teamId'))
WORKSPACE_ID = int(os.getenv('context.workspaceId'))
PROJECT_ID = int(os.getenv('modal.state.slyProjectId')) if os.getenv('modal.state.slyProjectId').isnumeric() else None

app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory=os.path.join(app_root_directory, 'static')), name="static")

templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))

DataJson()['current_step'] = 1

available_classes_names = []
selected_classes_list = []

project_dir = os.path.join(app_root_directory, 'tempfiles', 'project_dir')
output_project_dir = os.path.join(app_root_directory, 'tempfiles', 'output_project_dir')

output_project: sly.Project = None
output_project_meta: sly.ProjectMeta = None

project = {
    'workspace_id': 0,
    'project_id': 0
}

DataJson()['team_id'] = TEAM_ID
DataJson()['workspace_id'] = WORKSPACE_ID
DataJson()['instanceAddress'] = os.getenv('SERVER_ADDRESS')


model_data = {}
model_tag_suffix = ''


updated_images_ids = set()


