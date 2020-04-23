import sqlite3

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, ObjectProperty, BooleanProperty, StringProperty, DictProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.config import Config

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.recycleview import RecycleView
from kivy.uix.video import Video
from pathlib import Path

import Class_loader

Window.show_cursor = True
# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.

PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)


video_ids = []
video_name = ''

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)

class HeaderBox(BoxLayout):
    names = ObjectProperty()
    def __init__(self, **kwargs):
        super(HeaderBox, self).__init__(**kwargs)
        Clock.schedule_once(self.finish_init, 0)

    def finish_init(self, dt):
        self.clear_widgets()
        for elt in self.names:
            self.add_widget(Label(id = elt, text=elt))

class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    ''' Adds selection and focus behaviour to the view. '''


class TextInputBox(BoxLayout):
    data = ListProperty()

    def __init__(self, **kwargs):
        super(TextInputBox, self).__init__(**kwargs)
        Clock.schedule_once(self.finish_init, 0)

    def finish_init(self, dt):
        self.clear_widgets()
        for elt in self.data:
            self.add_widget(TextInput(id= elt['id']))

class SelectableLayout(RecycleDataViewBehavior, BoxLayout):
    row = ListProperty()
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(SelectableLayout, self).__init__(**kwargs)
        print("hello")
        Clock.schedule_once(self.finish_init, 0)

        # it delays the end of the initialization to the next frame, once the widget are already created
        # and the properties properly initialized

    def finish_init(self, dt):
        self.clear_widgets()
        for elt in self.row:
            self.add_widget(Label(id = elt, text=elt))
            # now, this works properly as the widget is already defined
        self.bind(row = self.update_row)


    def update_row(self, *args):
        # right now the update is rough, I delete all the widget and re-add them. Something more subtle
        # like only replacing the label which have changed
        #print(args)
        # because of the binding, the value which have changed are passed as a positional argument.
        # I use it to set the new value of the labels.
        self.clear_widgets()
        for elt in args[1]:
            self.add_widget(Label(id = elt, text = elt))


    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLayout, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLayout, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''

        self.selected = is_selected
        if self.selected:
            global video_name
            # assuming that last child is Label with name
            video_name = self.children[-1].text


class RV_video_from_database(BoxLayout):
    data_items = ListProperty([])
    current_selection = ObjectProperty()
    list_of_properties = ListProperty()

    def __init__(self, database, table = 'Stimulus', **kwargs):
        super(RV_video_from_database, self).__init__(**kwargs)
        self.database = database
        self.table = table

        # self.videos will have next structure :
        # {name1 : {key1 : value1, key2: value2 ,....}, name2 : {key1 : value1, key2: value2 ,....}, ....}
        self.videos = {}
        self.get_videos()

    def get_videos(self):
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()

        cursor.execute(f"SELECT name, meta_v FROM {self.table}")
        rows = cursor.fetchall()

        set_of_properties = set()

        # meta file has next structure:
        # key1 = value1
        # key2 = value2
        # ....
        # so here we parse it to self.videos
        for row in rows:
            data = []
            for idx, col in enumerate(row):
                # name column
                if idx == 0:
                    name = col
                    self.videos[col] = {}
                # meta file column
                elif idx == 1:
                    res = col.strip().split('\n')
                    for field_value in res:
                        key, value = field_value.split(' = ')
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                        set_of_properties.add(key)
                        self.videos[name][key] = value

        list_of_properties = list(sorted(set_of_properties))
        list_of_properties.insert(0, 'name')

        # if video has not got some key in its meta file, it will be initialized as None
        for video_key in self.videos:
            for field in list_of_properties[1:]:
                if field not in ([x for x in self.videos[video_key]]):
                    self.videos[video_key][field] = None

        self.list_of_properties = list_of_properties
        # appointing data for list of video in left side
        for name in self.videos.keys():
            video_row = list(map(lambda x: str(x), (self.videos[name].values())))
            video_row.insert(0, name)
            self.data_items.append(video_row)

    def sort_videos(self, key):
        new_data = sorted(self.videos.keys(), key = lambda x: self.videos[x][key])
        self.data_items = new_data

    def create_search_task(self):
        import re
        self.data_items = []
        search_task = {}
        for text_input in self.ids.TextInputBox_id.children:
            search_task[text_input.id] = text_input.text

        # if user add mask for name
        if search_task['name']:
            pattern = re.compile(search_task['name'].replace('*', '.*'))
        else:
            pattern = re.compile('.*')

        # list of keys which have conditions
        keys = [x for x in search_task.keys() if x != 'name' and search_task[x]]

        print('search task is ', search_task)
        print('keys are ', keys)

        # dict with format self.videos
        acceptable_videos = {}
        for video_key in self.videos.keys():
            if pattern.search(video_key):
                # due to filters have 'and' condition we initialize adding as 'True'
                # and if some key doesn't match according condition we set it as False
                video_to_add = True
                for key in keys:
                    if self.videos[video_key][key]:
                        diapason = list(map(lambda x: float(x), search_task[key].split(',')))
                        if self.videos[video_key][key] < diapason[0] or self.videos[video_key][key] > diapason[1]:
                            video_to_add = False
                if video_to_add:
                    acceptable_videos[video_key] = self.videos[video_key]

        for name in acceptable_videos.keys():
            video_row = list(map(lambda x: str(x), (self.videos[name].values())))
            video_row.insert(0, name)
            self.data_items.append(video_row)

        self.ids.r1.refresh_from_data()


video = Video()


class QuerySet(Screen):
    cnter = 0

    def __init__(self, database = 'Video_loader.db', table = 'Stimulus', **kwargs ):
        super(QuerySet, self).__init__(**kwargs)
        self.database = database
        self.table = table

        self.glay = BoxLayout()
        self.videolist  = RV_video_from_database("Video_loader.db")
        self.glay.add_widget(self.videolist)

        clay = BoxLayout(orientation =  'vertical')
        blay = BoxLayout(orientation = 'vertical')
        
        blay.add_widget(Button(text = 'Play', on_press = self.Play))
        blay.add_widget(Button(text = 'Append', on_press = self.Append))
        blay.add_widget(Button(text = 'Upload'))
        blay.add_widget(Button(text = 'Return'))
        
        self.vidlay = AnchorLayout()
        
        clay.add_widget(self.vidlay)
        clay.add_widget(blay)
        
        self.glay.add_widget(clay)
        self.tmp = RV()
        # tmp.add_widget(Label(text = 'asd'))
        self.glay.add_widget(self.tmp)

        self.add_widget(self.glay)

    def Append(self, instance):
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        sql_command = f"select id_v from {self.table} where name = '{video_name}'"
        cursor.execute(sql_command)
        data = cursor.fetchall()
        for row in data:
            video_ids.append(row[0])
        self.tmp.data.append({'text': str(video_name)})
        self.cnter = self.cnter+1

    def Play(self, instance):
        self.vidlay.clear_widgets()
        # path = self.filechoser.selection[0]
        path = r'sys_tmp' + rf'\{video_name}'
        print(path)
        loader = Class_loader.Video_loader(self.database)
        loader.download_video(video_name, path)
        video.source = path
        self.vidlay.add_widget(video)
        video.state = 'play'

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        