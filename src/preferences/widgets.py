from supervisely.app import DataJson, StateJson
from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel, NotificationBox, GridGallery

import src.sly_globals as g

select_preferences_button = ElementButton(text='confirm preferences')
reselect_preferences_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect preferences', button_type='warning', button_size='small', plain=True)

preview_results_button = ElementButton(text='<i class="zmdi zmdi-collection-image" style="margin-right: 5px"></i> preview results', button_type='warning', button_size='small')
preview_results_button.disabled = True

preview_grid_gallery = GridGallery(columns_number=3, show_opacity_slider=False, sync_views=True)

labeling_progress = SlyTqdm()
labeling_done_label = DoneLabel(text='done')

start_labeling_button = ElementButton(text='Apply Classifier to Images Project')
