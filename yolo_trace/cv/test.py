import cv2
import time
# 摄像头类
class Camera:
    def __init__(self, device_id=0):
       self.cap = None
        
    # 创建摄像头
    def open(self, device_id = 0):
        if self.isOpened():
            print("摄像头已经开启...")
            return
        self.cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
        # 尝试设置摄像头的捕获格式为MJPEG
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        # 设置捕获的分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # 设置帧率
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        # 打印出分辨率
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print("width:", width)
        print("height:", height)
        print("fps:", fps)
        
        
    def read(self):
        return self.cap.read()
    
    def release(self):
        self.cap.release()
        
    def isOpened(self):
        if self.cap == None:
            return False
        return self.cap.isOpened()    


cap = Camera()
cap.open()

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()
    
# 循环读取摄像头帧
while True:
    prev_frame_time = time.time()
    ret, frame = cap.read()
    # 如果正确读取帧，ret为True
    if not ret:
        print("无法读取帧")
        break
    # 计算帧率
    current_time = time.time()
    fps = 1 / (current_time - prev_frame_time)
    # 将帧率显示在帧上
    fps_display = "FPS: {:.2f}".format(fps)
    cv2.putText(frame, fps_display, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 2, cv2.LINE_AA)
    # 显示帧
    cv2.imshow('CSI Camera', frame)

    # 按 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头资源
cap.release()
# 关闭所有 OpenCV 窗口
cv2.destroyAllWindows()