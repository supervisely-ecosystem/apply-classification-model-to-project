from fastapi import Request, Depends
from supervisely.app.fastapi import available_after_shutdown

import src.sly_globals as g

import src.select_input_projects
import src.connect_to_model
import src.preferences


@g.app.get("/")
@available_after_shutdown(app=g.app)
def read_index(request: Request = None):
    return g.templates_env.TemplateResponse('index.html', {'request': request})

@g.app.on_event("shutdown")
def shutdown():
    read_index()  # save last version of static files
