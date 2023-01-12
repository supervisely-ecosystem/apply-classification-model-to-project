from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel, NotificationBox, GridGallery

import src.sly_globals as g

select_preferences_button = ElementButton(text='confirm preferences', widget_id="select_preferences_button")
reselect_preferences_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect preferences', button_type='warning', button_size='small', plain=True, widget_id="reselect_preferences_button")

preview_results_button = ElementButton(text='<i class="zmdi zmdi-collection-image" style="margin-right: 5px"></i> preview results', button_type='warning', button_size='small', widget_id="preview_results_button")
preview_results_button.disabled = True

preview_grid_gallery = GridGallery(columns_number=3, show_opacity_slider=False, sync_views=True, widget_id="preview_grid_gallery")

labeling_progress = SlyTqdm(widget_id="labeling_progress")
labeling_done_label = DoneLabel(text='done', widget_id="labeling_done_label")

select_all_classes_button = ElementButton(text='<i class="zmdi zmdi-check-all"></i> SELECT ALL', button_type='text', button_size='mini', plain=True, widget_id="select_all_classes_button")
deselect_all_classes_button = ElementButton(text='<i class="zmdi zmdi-square-o"></i> DESELECT ALL', button_type='text', button_size='mini', plain=True, widget_id="deselect_all_classes_button")

start_labeling_button = ElementButton(text='Apply Classifier to Images Project', widget_id="start_labeling_button")
