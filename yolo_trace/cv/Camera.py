import cv2

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
        
        self.cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 4000)
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
        print("释放cam")
        self.cap.release()
        
    def isOpened(self):
        if self.cap == None:
            return False
        return self.cap.isOpened()    
