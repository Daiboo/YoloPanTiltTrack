import threading
from adafruit_servokit import ServoKit
from config import *


class PID:
    def __init__(self, P, I, D):
        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.previous_error = 0
        self.integral = 0

    def compute(self, set_point, measured_value):
        error = measured_value - set_point 
        self.integral += error
        derivative = error - self.previous_error
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.previous_error = error
        return output

    # 更新pid
    def update_pid(self, P, I, D):
        self.Kp = P
        self.Ki = I
        self.Kd = D
        
    def get_p(self):
        return self.Kp
    def get_i(self):
        return self.Ki
    
    def get_d(self):
        return self.Kd
    
    def set_p(self, P):
        self.Kp = P
    def set_i(self, I):
        self.Ki = I
    def set_d(self, D):
        self.Kd = D

class YuntaiTrack:
    def __init__(self):
        self.kit = ServoKit(channels=16)
        self.pan_pid = PID(0.022, 0.0, 0.013) 
        self.tilt_pid = PID(0.022, 0.0, 0.013)
        self.pan_servo = 0   # 水平舵机在通道0
        self.tilt_servo = 1  # 垂直舵机在通道1
        # self.kalman_filter_x = KalmanFilter(1, 0.1, 0.2)
        # self.kalman_filter_y = KalmanFilter(1, 0.1, 0.2)
        # 初始化舵机位置
        self.kit.servo[self.pan_servo].angle = 90
        self.kit.servo[self.tilt_servo].angle = 90
        
        
    def track(self, target_x, target_y, img_width, img_height):
        # 计算目标与图像中心的偏差
        error_x = target_x - (img_width / 2)
        error_y = target_y - (img_height / 2)
        # 使用卡尔曼滤波器预测目标位置
        # self.kalman_filter_x.predict()
        # self.kalman_filter_y.predict()
        
        # # 更新滤波器状态
        # self.kalman_filter_x.update(error_x)
        # self.kalman_filter_y.update(error_y)
        
        # 获取滤波后的位置偏差
        # filtered_error_x = self.kalman_filter_x.get_current_estimate()
        # filtered_error_y = self.kalman_filter_y.get_current_estimate()
        
        # PID算法计算舵机调整角度
        pan_adjust = self.pan_pid.compute(0, error_x)
        tilt_adjust = self.tilt_pid.compute(0, error_y)


        # 更新舵机角度
        current_pan_angle = self.kit.servo[self.pan_servo].angle
        current_tilt_angle = self.kit.servo[self.tilt_servo].angle


        new_pan_angle = current_pan_angle + pan_adjust
        new_tilt_angle = current_tilt_angle - tilt_adjust
        
        # 限制角度范围
        new_pan_angle = max(min(new_pan_angle, 180), 0)
        new_tilt_angle = max(min(new_tilt_angle, 180), 60)

        self.kit.servo[self.pan_servo].angle = new_pan_angle
        self.kit.servo[self.tilt_servo].angle = new_tilt_angle


class YuntaiThread(threading.Thread):
    def __init__(self, yuntai_track, img_width, img_height):
        super().__init__()
        self.yuntai_track = yuntai_track
        self.img_width = img_width
        self.img_height = img_height
        self.target_x = None
        self.target_y = None
        self.target_name = None
        self.run_start = False
        self.lock = threading.Lock()            
        self.condition = threading.Condition()  # 用于等待/通知机制
        self.stop_event = threading.Event()     
        
    def set_target_name(self, target_name):
        with self.lock:
            self.target_name = target_name

    def handle_infer_result(self, infer_result):
        if(self.target_name == None):
            return
        
        boxs = infer_result["boxs"]
        classid = infer_result["classid"]
        if len(boxs) <= 0:
            return
        
        for i in range(len(boxs)):
            if categories[int(classid[i])] == self.target_name:
                x1, y1, x2, y2 = boxs[i]
                self.target_x = (x1 + x2) / 2
                self.target_y = (y1 + y2) / 2
                with self.condition:
                    self.condition.notify()  # 通知run方法开始跟踪
                break
        else:
            self.target_x = None
            self.target_y = None
            return
        # print("目标位置：", self.target_x, self.target_y)
          
    def run(self):
        while not self.stop_event.is_set():
            with self.condition:
                self.condition.wait()  # 等待handle_infer_result的通知
            if self.target_x is not None and self.target_y is not None:
                self.yuntai_track.track(self.target_x, self.target_y, self.img_width, self.img_height)
            
    def stop(self):
        self.stop_event.set()
        with self.condition:
            self.condition.notify()  # 确保如果run方法正在等待，它能够退出等待状态    
