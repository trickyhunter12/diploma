import sys
import threading
import time
import PySimpleGUI as sg
from PIL import Image, ImageTk
import subprocess
import os
from helper_classes import  VideoReader


class MyWindow:

    def __init__(self):

    
        self.interpreter = None
        self.interpreter_event = threading.Event()
    #    self.interpreter_event.clear()
        self.top1_result = ''
        self.top4_result = ''

        # ==== VIDEO HANDLING ====#
        self.vReader = None
        self.image = None
        self.video = ''
        self.play_pause_event = threading.Event()
    #    self.play_pause_event.clear()
        self.video_length = 0
        self.cur_frame = 0
        self.v_height = 500
        self.v_width = 500

        # ==== GUI ====#
        sg.theme('DarkBlue3')
        controls_column = [

            # ==== FILE BROWSER ====#
            [sg.Text('Choose video file:')],
            [sg.In(size=(45, 1), enable_events=True, readonly=True, key="-VIDEO-BROWSER-"),
             sg.FileBrowse()],
            
            [sg.Text('Choose output folder:')],
            [sg.In(size=(45, 1), enable_events=True, readonly=True, key="-OUTPUT-BROWSER-"),
             sg.FolderBrowse()],

            # ==== TOP4ACC ====#
            [sg.Text('Ordered accuracy:')],
            [sg.Output(size=(45, 6), key="-4-RESULTS-")],
            [sg.Text('Perform recognition'), sg.Button('Start', key="-RECOGNIZE-")],

        ]

        # ==== VIDEO DISPLAY ====#
        video_display_column1 = [
            [sg.Canvas(size=(500, 300), key="-DISPLAY-", background_color='black')],

            # ==== VIDEO CONTROLS ====#
            [sg.Slider(range=(0, 0), orientation='horizontal', size=(63, 10), key="-SLIDER-", enable_events=True)],
            [sg.Button('Play', key="-PLAY-"),
             sg.Button('Pause', key="-PAUSE-"),
             sg.Button('Full screen', key="-FULL-"),
             sg.Button('Back', key="-Back-", visible= False)]
        ]

        layout1 = [
            [sg.Column(controls_column, vertical_alignment='top', key='-COL1-'),
             sg.Column(video_display_column1, key='-COL2-')],
            [sg.Button("Exit", size=(10, 1))]
        ]
        
        
        # layout = [sg.Column(layout1, key='-COL1-'), sg.Column(layout2, visible=False, key='-COL2-')]
        
        layout = 1
        self.window = sg.Window(
            "main",
            layout1,
            location=(0, 0),
            finalize=True,
            resizable=True,
            auto_size_text=True,
            auto_size_buttons=True,
            element_justification="left",
            font="Courier 12").Finalize()
        
        self.window.Maximize()
        display = self.window.Element("-DISPLAY-")
        self.display = display.TKCanvas

        self.interpreter_thread()
        self.video_thread()
        self.out_path = ''
        # self.interpreter = Interpreter(networks, labels, device)

        while True:
            event, values = self.window.Read()

            if event == sg.WIN_CLOSED or event == "Exit":
                break

            if event == "-VIDEO-BROWSER-":
                if values["-VIDEO-BROWSER-"] != self.video:
                    self.video = values["-VIDEO-BROWSER-"]
                    try:
                        self.vReader = VideoReader(self.video, norm=500)     # norm -> normalization
                        self.top1_result, self.top4_result = None, None
                        self.v_height = self.vReader.NORM_HEIGHT
                        self.display.config(width=self.v_width, height=self.v_height)
                        self.window["-VIDEO-BROWSER-"].update(self.video)
                        self.window["-SLIDER-"].update(range=(0, self.vReader.FRAMES))
                        self.cur_frame = 0
                    except ZeroDivisionError as err:
                        print(err)

            if event == "-OUTPUT-BROWSER-":
                self.out_path = values["-OUTPUT-BROWSER-"]

            if event == "-NETWORK-":
                self.net = values["-NETWORK-"]
                self.window["-NETWORK-NAME-"].update(self.net)

            if event == "-RECOGNIZE-":
                self.interpreter_event.set()
            
            if event == "-FULL-":
                self.window["-COL1-"].update(visible=False)
                self.window["-DISPLAY-"].set_size((1000, 530))
                self.v_width = 1000
                self.v_height = 530
                time.sleep(1)
                self.cur_frame = 0
                self.window["-FULL-"].update(visible=False)
                self.window["-Back-"].update(visible=True)
                # self.window["-COL2-"].update(visible=True)
                
            if event == "-Back-":
                self.window["-COL2-"].update(visible=False)
                self.window["-COL1-"].update(visible=True)
                self.window["-COL2-"].update(visible=True)
                self.window["-DISPLAY-"].set_size((500, 300))
                self.v_width = 500
                self.v_height = 300
                time.sleep(1)
                self.cur_frame = 0
                self.window["-Back-"].update(visible=False)
                self.window["-FULL-"].update(visible=True)
                
            if event == "-PLAY-":
                if self.vReader:
                    self.play_pause_event.set()

            if event == "-PAUSE-":
                if self.vReader:
                    self.play_pause_event.clear()

            if event == "-SLIDER-":
                self.wanted_frame = values["-SLIDER-"]
                self.set_frame(self.wanted_frame)

        self.window.close()
        sys.exit()

    def video_thread(self):
        t = threading.Thread(target=self.play_video)
        t.daemon = True
        t.start()

    def interpreter_thread(self):
        t = threading.Thread(target=self.interpret_video)
#        t.daemon = True
        t.start()

    def interpret_video(self):
        while self:
            self.interpreter_event.wait()
            if self.vReader:
                if self.out_path =='':
                    self.window["-4-RESULTS-"].update('creating output dir...')
                    cwd = os.getcwd()
                    if not os.path.exists(f'{cwd}/output'):
                        os.makedirs(f'{cwd}/output')
                    self.out_path = os.getcwd()+'/output'
                if not os.path.exists(self.out_path):
                    self.window["-4-RESULTS-"].update('dir not exist...')
                else:
                    self.window["-4-RESULTS-"].update('recognizing... \n')
                    self.runCommand(window = self.window,input_video = self.video, output_path = self.out_path)
                    # self.window["-4-RESULTS-"].update(self.res)
                    self.interpreter_event.clear()
            else:
                self.window["-4-RESULTS-"].update('Nothing to recognize.')
                self.window["-4-RESULTS-"].update('Choose video of mp4 or avi formats.')
                self.interpreter_event.clear()  


    def play_video(self):
        if self.play_pause_event.is_set():
            start_time = time.time()

            if self.vReader:
                ret, frame = self.vReader.play_video(top1acc=self.top1_result)

                if ret:
                    self.image = ImageTk.PhotoImage(
                        image=Image.fromarray(frame).resize((self.v_width, self.v_height), Image.NEAREST))
                    self.display.create_image(0, 0, image=self.image, anchor='nw')

                    self.cur_frame += 1
                    self.window["-SLIDER-"].update(value=self.cur_frame)

                self.display.after(abs(int((self.vReader.DELAY - (time.time() - start_time)) * 1000)), self.play_video)
                return

        self.display.after(200, self.play_video)
        return

    def set_frame(self, wanted_frame):
        if self.vReader:
            ret, frame = self.vReader.set_frame(wanted_frame, top1acc=self.top1_result)
            self.cur_frame = wanted_frame
            self.window["-SLIDER-"].update(value=self.cur_frame)
            if ret:
                self.image = ImageTk.PhotoImage(
                    image=Image.fromarray(frame).resize((self.v_width, self.v_height), Image.NEAREST))
                self.display.create_image(0, 0, image=self.image, anchor='nw')
        return

    # This function does the actual "running" of the command.  Also watches for any output. If found output is printed
    def runCommand(self, timeout=None, window=None, input_video=None, output_path=None):
        p = subprocess.Popen(f"python test.py {input_video} {output_path}/output.mp4", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
        for line in p.stdout:
            line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').rstrip()
            # if not line[0].islower():
            output += line
            print(line)
            window.Refresh() if window else None    
        retval = p.wait(timeout)
        
        self.video = f"{output_path}/output.mp4"
        self.vReader = VideoReader(self.video, norm=500)
        self.v_height = self.vReader.NORM_HEIGHT
        self.display.config(width=self.v_width, height=self.v_height)
        self.window["-VIDEO-BROWSER-"].update(self.video)
        self.window["-SLIDER-"].update(range=(0, self.vReader.FRAMES))
        return (retval, output)                         # also return the output just for fun

if __name__ == '__main__':
    MyWindow()
