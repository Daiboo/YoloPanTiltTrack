from config import *

import ctypes
import os

from yolov5.Yolov5TRT import *
from cv.Camera import *
from cv.video import *
from pan_tilt.PanTilt import *
from voice.Audio import *


from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSlider, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap


        

    
class App(QWidget):
    def __init__(self, yolov5_wrapper, cam, yuntai):
        super().__init__()
        self.setWindowTitle("PyQt YOLOv5 Trace")
        # 是否加载模型
        self.yolov5_wrapper = yolov5_wrapper
        self.disply_width = 700
        self.display_height = 500
        self.load_model_status = False
        
        # 设置窗口的初始大小
        self.resize(self.disply_width, self.display_height)
        
        
        self.image_label = QLabel(self)
        self.image_label.resize(640, 480)
        self.cam_closed_pixmap = QPixmap("source/cam_closed.png")
        print("pin_map_size:", self.cam_closed_pixmap.size())
        
        self.image_label.setPixmap(self.cam_closed_pixmap)
        
        self.video_thread = VideoThread(yolov5_wrapper, cam)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        
        self.yuntai = yuntai
        self.yuntai_thread = YuntaiThread(yuntai, 640, 480)
        self.video_thread.infer_results_signal.connect(self.yuntai_thread.handle_infer_result)
        
        self.yuntai_thread.start()
        
        self.audio_thread = AudioThread(APP_ID, API_KEY, SECRET_KEY)
        self.audio_thread.recognition_result_signal.connect(self.handle_recognition_result)
        self.audio_thread.begin_record_signal.connect(self.show_voice_begin_label)
        self.audio_thread.end_record_signal.connect(self.show_voice_end_label)
        # self.audio_thread.start()


        model_h_layout = QHBoxLayout()
        self.load_model_Button = QPushButton("加载模型", self)
        self.load_model_Button.clicked.connect(self.load_model)
        self.infer_button = QPushButton("开启推理", self)
        self.infer_button.setDisabled(True)
        self.infer_button.clicked.connect(self.inference_toggle)
        model_h_layout.addWidget(self.load_model_Button)
        model_h_layout.addWidget(self.infer_button)
        
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('开启摄像头', self)
        self.start_button.clicked.connect(self.start_cam)
        self.stop_button = QPushButton('关闭摄像头', self)
        self.stop_button.clicked.connect(self.stop_cam)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        # pid 滑块控制
        # 创建P滑块
        p_h_layout = QHBoxLayout()
        self.p_value_label = QLabel(self)
        self.p_slider = QSlider(Qt.Horizontal, self)
        self.p_slider.setMinimum(0)
        self.p_slider.setMaximum(100)
        self.p_slider.setValue(self.yuntai.pan_pid.get_p() * 1000)  # 假设初始值为15
        self.p_value_label.setText("P: {:.3f}".format(self.yuntai.pan_pid.get_p()))  # 初始显示当前值
        self.p_slider.valueChanged.connect(self.p_value_changed)
        p_h_layout.addWidget(self.p_value_label)
        p_h_layout.addWidget(self.p_slider)

        # 创建I滑块
        
        i_h_layout = QHBoxLayout()
        self.i_value_label = QLabel(self)
        self.i_slider = QSlider(Qt.Horizontal, self)
        self.i_slider.setMinimum(0)
        self.i_slider.setMaximum(100)
        self.i_slider.setValue(self.yuntai.pan_pid.get_i() * 1000)  # 假设初始值为15
        self.i_value_label.setText("I: {:.3f}".format(self.yuntai.pan_pid.get_i()))  # 初始显示当前值
        self.i_slider.valueChanged.connect(self.i_value_changed)
        i_h_layout.addWidget(self.i_value_label)
        i_h_layout.addWidget(self.i_slider)

        # 创建D滑块
        d_h_layout = QHBoxLayout()
        self.d_value_label = QLabel(self)
        self.d_slider = QSlider(Qt.Horizontal, self)
        self.d_slider.setMinimum(0)
        self.d_slider.setMaximum(100)
        self.d_slider.setValue(self.yuntai.pan_pid.get_d() * 1000)  # 假设初始值为10
        self.d_value_label.setText("D: {:.3f}".format(self.yuntai.pan_pid.get_d()))
        self.d_slider.valueChanged.connect(self.d_value_changed)
        d_h_layout.addWidget(self.d_value_label)
        d_h_layout.addWidget(self.d_slider)
        
        # 左边显示界面
        sub_main_left_layout = QVBoxLayout()
        sub_main_left_layout.addWidget(self.image_label)
        sub_main_left_layout.addLayout(model_h_layout)
        sub_main_left_layout.addLayout(button_layout)
        sub_main_left_layout.addLayout(p_h_layout)
        sub_main_left_layout.addLayout(i_h_layout)
        sub_main_left_layout.addLayout(d_h_layout)
        
        # 右边显示界面
        self.sub_main_right_layout = QVBoxLayout()
        self.sub_main_right_layout.setAlignment(Qt.AlignTop)
        self.create_button_group()
        
        self.show_target_label = QLabel(self)
        self.show_target_label.setText("当前目标: None")
        # self.show_target_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.show_target_label.setAlignment(Qt.AlignTop)
        self.show_target_label.setMinimumHeight(30)
        self.show_target_label.setMaximumHeight(30)
        
        # 添加弹簧控件
        # self.sub_main_right_layout.addStretch(1)
        
        # 使用说明
        explain = "使用说明(可语音识别):\n" \
                    "1. 开启语音识别(可选) \n" \
                    "2. 加载模型\n" \
                    "3. 开启摄像头\n" \
                    "4. 开启推理\n" \
                    "5. 追踪目标\n" \
                    "  目标可为：盒子、杯子、固体胶、手机\n" \
                    "6. 关闭推理\n" \
                    "7. 关闭摄像头\n" \
                    "8. 关闭语音识别(可选)\n" \
                    "Author: 2101630206高代波\n"  \
                    "Time:            2024-7-24"
      
        explain_label = QLabel(explain, self)
        
        # 语音开启关闭按钮
        voice_buttion_h_layout = QHBoxLayout()
        self.begin_voice_button = QPushButton("语音识别ON")
        self.end_voice_button = QPushButton("语音识别OFF")
        self.begin_voice_button.setDisabled(False)
        self.end_voice_button.setDisabled(True)
        self.begin_voice_button.clicked.connect(self.voice_begin)
        self.end_voice_button.clicked.connect(self.voice_end)
        voice_buttion_h_layout.addWidget(self.begin_voice_button)
        voice_buttion_h_layout.addWidget(self.end_voice_button)
        

        # 语音进度条
        voice_label_h_layout = QHBoxLayout()
        self.begin_voice_label = QLabel("开始录音", self)
        self.end_voice_label = QLabel("录音结束", self)
        self.begin_voice_label.setFixedHeight(80)
        self.end_voice_label.setFixedHeight(80)
        voice_label_h_layout.addWidget(self.begin_voice_label)
        voice_label_h_layout.addWidget(self.end_voice_label)
        
        
        self.voice_label = QLabel("语音指令: None",self)
        # self.voice_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.voice_label.setMaximumHeight(100)

        self.sub_main_right_layout.addWidget(self.show_target_label)
        self.sub_main_right_layout.addWidget(explain_label)
        self.sub_main_right_layout.addLayout(voice_buttion_h_layout)
        self.sub_main_right_layout.addLayout(voice_label_h_layout)
        self.sub_main_right_layout.addWidget(self.voice_label)
        
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(sub_main_left_layout)
        self.main_layout.addLayout(self.sub_main_right_layout)
        self.setLayout(self.main_layout)
        
    # 创建按钮组的方法
    def create_button_group(self):
        self.category_buttons = []  # 用于存储按钮的列表，以便后续可以修改它们的属性

        # 创建两行按钮的布局
        top_row_layout = QHBoxLayout()
        bottom_row_layout = QHBoxLayout()

        # 分配按钮到两行
        for i, category in enumerate(categories):
            button = QPushButton(category, self)
            button.setFixedHeight(80)
            button.clicked.connect(lambda checked, category=category: self.set_target_name(category))
            self.category_buttons.append(button)

            # 前两个按钮放在顶部行，其余放在底部行
            if i < 2:
                top_row_layout.addWidget(button)
            else:
                bottom_row_layout.addWidget(button)

        # 将两行按钮布局添加到主布局
        button_layout = QVBoxLayout()
        button_layout.addLayout(top_row_layout)
        button_layout.addLayout(bottom_row_layout)
        # 将按钮布局添加到现有的布局中
        self.sub_main_right_layout.addLayout(button_layout)  # 你需要根据你的代码结构调整这一行
        # 连接信号以更新按钮颜色
        self.video_thread.infer_results_signal.connect(self.update_button_colors) 

    def voice_begin(self):
        self.begin_voice_button.setDisabled(True)
        self.end_voice_button.setDisabled(False)
        self.audio_thread.start()
    def voice_end(self):
        self.begin_voice_button.setDisabled(False)
        self.end_voice_button.setDisabled(True)
        self.audio_thread.stop()
        
    def show_voice_begin_label(self, text):
        self.begin_voice_label.setText(text)
        self.end_voice_label.setText("")
        
    def show_voice_end_label(self, text):
        self.end_voice_label.setText(text)
        self.begin_voice_label.setText("")
        

    def handle_recognition_result(self, text):
        # 摄像头
        if "开启摄像头" in text:
            self.voice_label.setText("语音指令: 开启摄像头")
            self.start_cam()
        elif "关闭摄像头" in text:
            self.voice_label.setText("语音指令: 关闭摄像头")
            self.stop_cam()
        elif "加载模型" in text:
            self.voice_label.setText("语音指令: 加载模型")
            self.load_model()
        elif "开启推理" in text:
            self.voice_label.setText("语音指令: 开启推理")
            self.inference_toggle()
        elif "关闭推理" in text:
            self.voice_label.setText("语音指令: 关闭推理")
            self.inference_toggle()
        elif "关闭语音识别" in text:
            self.voice_label.setText("语音指令: 关闭语音识别")
            self.voice_end()
        elif "跟踪" in text or "追踪" in text or "最终":
            if "盒子" in text or "合" in text:
                self.voice_label.setText("语音指令: 追踪盒子")
                self.set_target_name("box")
            elif "杯子" in text:
                self.voice_label.setText("语音指令: 追踪杯子")
                self.set_target_name("cup")
            elif "固体胶" in text:
                self.voice_label.setText("语音指令: 追踪固体胶")
                self.set_target_name("glue-stick")
            elif "手机" in text:
                self.voice_label.setText("语音指令: 追踪手机")
                self.set_target_name("phone")

            
                    
    def update_image(self, cv_img):
        qt_img = QPixmap.fromImage(cv_img)
        self.image_label.setPixmap(qt_img)
        
    def start_cam(self):
        if not self.video_thread.isRunning():
            self.video_thread.start()
        
    # 更新按钮颜色的方法
    def update_button_colors(self, infer_result):
        # 清空所有按钮的颜色
        for button in self.category_buttons:
            button.setStyleSheet("")
        # 获取推理结果
        classid = infer_result["classid"]
        for class_id in classid:
            # 根据类别ID设置按钮的颜色
            self.category_buttons[int(class_id)].setStyleSheet("background-color: yellow")

    def set_target_name(self, target_name):
        target = target_name
        if self.yuntai_thread.target_name == target_name:
            target = None
        self.yuntai_thread.set_target_name(target)
        print("设置目标为{}".format(target))
        self.show_target_label.setText("当前目标：{}".format(target))

        
    def stop_cam(self):
        self.video_thread.stop()
        
    
    def load_model(self):
        if not self.yolov5_wrapper.load_model_status:
           self.yolov5_wrapper.load_model()
           self.load_model_status = True
           self.infer_button.setDisabled(False)
           self.load_model_Button.setDisabled(True)
           
        else:
            print("模型已经加载")
    
    def inference_toggle(self):
        if self.video_thread.infer:
            self.video_thread.infer = False
            self.infer_button.setText("开启推理")
        else:
            self.video_thread.infer = True
            self.infer_button.setText("关闭推理")
    
    def p_value_changed(self, value):
        # 这里可以根据滑动条的值调整PID参数
        self.yuntai.pan_pid.set_p(value / 1000)
        self.yuntai.tilt_pid.set_p(value / 1000)
        # 显示
        self.p_value_label.setText("P: {:.3f}".format(value / 1000))
        
    def i_value_changed(self, value):
        # 这里可以根据滑动条的值调整PID参数
        self.yuntai.pan_pid.set_i(value / 1000)
        self.yuntai.tilt_pid.set_i(value / 1000)
        # 显示
        self.i_value_label.setText("I: {:.3f}".format(value / 1000))
        
    def d_value_changed(self, value):
        # 这里可以根据滑动条的值调整PID参数
        self.yuntai.pan_pid.set_d(value / 1000)
        self.yuntai.tilt_pid.set_d(value / 1000)
        # 显示
        self.d_value_label.setText("D: {:.3f}".format(value / 1000))
        
    def closeEvent(self, event):
        # 在这里添加你的清理代码
        print("应用程序正在关闭，执行清理工作...")
        self.video_thread.stop()
        time.sleep(1)
        yolov5_wrapper.destroy()
        self.yuntai_thread.stop()
        self.audio_thread.stop()
        # 释放资源的代码
        if cam.isOpened():
            cam.release()

        # 确保调用基类的closeEvent
        super().closeEvent(event) 

if __name__ == "__main__":

    ctypes.CDLL(PLUGIN_LIBRARY)

    # a YoLov5TRT instance
    yolov5_wrapper = YoLov5TRT(engine_file_path)
    # 定义摄像头ID
    device_id = 0
    # 创建视频捕获对象
    cam = Camera(device_id)

    yuntai = YuntaiTrack()

    try:
        app = QApplication(sys.argv)
        a = App(yolov5_wrapper, cam, yuntai)
        a.show()
        sys.exit(app.exec_())
        
        
    except Exception as e:
        print(f"发生异常: {e}")
    finally:

        print("资源已释放")
