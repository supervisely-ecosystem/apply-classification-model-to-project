from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel, NotificationBox

import src.sly_globals as g

select_preferences_button = ElementButton(text='start labeling')

reselect_preferences_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect', button_type='warning', button_size='small', plain=True)

labeling_progress = SlyTqdm()

labeling_done_label = DoneLabel(text='done')
