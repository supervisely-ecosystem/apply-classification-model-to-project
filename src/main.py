from fastapi import Request, Depends

import src.sly_globals as g

import src.select_input_projects
import src.connect_to_model
import src.preferences


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request})

