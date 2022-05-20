import os
from pathlib import Path

from fastapi import FastAPI

from supervisely import FileCache
from supervisely.app import DataJson
from supervisely.sly_logger import logger
from starlette.staticfiles import StaticFiles

import supervisely
from supervisely.app.fastapi import create, Jinja2Templates

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")

app_cache_dir = os.path.join(app_root_directory, 'tempfiles', 'cache')

api: supervisely.Api = supervisely.Api.from_env()
file_cache = FileCache(name="FileCache", storage_root=app_cache_dir)
app = FastAPI()
sly_app = create()

TEAM_ID = os.getenv('context.teamId')
WORKSPACE_ID = os.getenv('context.workspaceId')

app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory=os.path.join(app_root_directory, 'static')), name="static")

templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))

DataJson()['current_step'] = 1


project_dir = os.path.join(app_root_directory, 'tempfiles', 'gt_project_dir')
project = {
    'workspace_id': 0,
    'project_id': 0
}

DataJson()['team_id'] = TEAM_ID
DataJson()['workspace_id'] = WORKSPACE_ID


model_data = {}
