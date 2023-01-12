from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel, NotificationBox

import src.sly_globals as g

connect_model_button = ElementButton(text='CONNECT', button_type='primary', widget_id="connect_model_button")
reselect_model_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>connect to another model', button_type='warning', button_size='small', plain=True, widget_id="reselect_model_button")
model_selected_done_label = DoneLabel(text='successfully connected', widget_id="model_selected_done_label")

toggle_all_previews_button = ElementButton(text='show all', plain=True, button_size='small', widget_id="toggle_all_previews_button")


connect_model_notification_box = NotificationBox(description='Select served Classification model from list below', widget_id="connect_model_notification_box")
model_classes_notification_box = NotificationBox(title='Model available Classes', description='images preview of the classes the model predicts', widget_id="model_classes_notification_box")
model_info_notification_box = NotificationBox(description='Model Info', widget_id="model_info_notification_box")
