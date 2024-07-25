import cv2
import os
import time
import threading

delay_capture = False  # True表示开启延时拍照，False表示关闭
delay_seconds = 5  # 延时5秒

# 定义摄像头ID
device_id = 0
# 创建视频捕获对象
cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)

# 尝试设置摄像头的捕获格式为MJPEG
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

# 设置捕获的分辨率
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# 设置帧率
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 指定保存图片的目录
save_dir = "captured_images_640_480"
# 如果目录不存在，则创建它
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

print("按 's' 键保存图片")

def capture_photo(delay_seconds, save_dir, frame_counter):
    print(f"延时{delay_seconds}秒后拍照")
    time.sleep(delay_seconds)  # 延时
    ret, frame = cap.read()  # 延时后再次读取帧
    frame = cv2.flip(frame, 1)  # 如果需要，再次翻转帧
    if not ret:
        print("延时后无法读取摄像头帧，跳过...")
        return
    img_name = f"captured_frame_{frame_counter}.jpg"
    cv2.imwrite(os.path.join(save_dir, img_name), frame)
    print(f"{img_name} 已保存至 {save_dir}。")

# 获取文件夹下已保存的图片数量
frame_counter = len(os.listdir(save_dir))
while True:
    # 从摄像头读取帧
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not ret:
        print("无法读取摄像头帧，退出...")
        break

    # 显示帧
    cv2.imshow('Camera', frame)

    key = cv2.waitKey(1) & 0xFF
    # 在主循环中
    if key == ord('s'):
        if delay_capture:
            # 创建并启动拍照线程
            threading.Thread(target=capture_photo, args=(delay_seconds, save_dir, frame_counter)).start()
            frame_counter += 1
        else:
            # 如果不使用延时，直接在主线程中处理拍照逻辑
            img_name = f"captured_frame_{frame_counter}.jpg"
            cv2.imwrite(os.path.join(save_dir, img_name), frame)
            print(f"{img_name} 已保存至 {save_dir}。")
            frame_counter += 1

cap.release()
cv2.destroyAllWindows()
