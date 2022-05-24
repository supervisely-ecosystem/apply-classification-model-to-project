from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel, NotificationBox

import src.sly_globals as g

connect_model_button = ElementButton(text='CONNECT', button_type='primary')
reselect_model_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect', button_type='warning', button_size='small', plain=True)
model_selected_done_label = DoneLabel(text='successfully connected')

toggle_all_previews_button = ElementButton(text='show all', plain=True, button_size='small')


connect_model_notification_box = NotificationBox(description='Select served Classification model from list below')
model_classes_notification_box = NotificationBox(title='Model available Classes', description='images preview of the classes the model predicts')
model_info_notification_box = NotificationBox(description='Model Info')
