import threading
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import time
import cv2


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    infer_results_signal = pyqtSignal(dict)
    
    def __init__(self, yolov5_wrapper, cam):
        super().__init__()
        self._run_flag = True
        self.infer = False
        self.yolov5_wrapper = yolov5_wrapper
        self.cam = cam
        self.cam_closed_pixmap = QPixmap("source/cam_closed.png")
    

    def run(self):
        if not self.cam.isOpened():  
            self.cam.open()  
        cam = self.cam
        while self._run_flag:
            prev_time = time.time()
            ret, frame = cam.read()
            frame = cv2.flip(frame, 1)
            if ret:
                if self.infer:
                    # 推理
                    result, used_t, result_boxs, result_classid = self.yolov5_wrapper.infer(frame)
                    infer_results = {"boxs": result_boxs, "classid": result_classid}
                    self.infer_results_signal.emit(infer_results)
                    frame = result
                    
                # 帧率
                current_time = time.time()
                fps = 1 / (current_time - prev_time)
            

                cv2.putText(frame, str(int(fps)), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 3, cv2.LINE_AA)

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.change_pixmap_signal.emit(convert_to_Qt_format)
                
        self.change_pixmap_signal.emit(self.cam_closed_pixmap.toImage())
        cam.release()

    def stop(self):
        self._run_flag = False
        self.wait()
    
    def start(self):
        self._run_flag = True
        # 父类start函数
        super().start()
