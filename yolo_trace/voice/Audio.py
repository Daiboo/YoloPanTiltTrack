
import threading
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from aip import AipSpeech
import pyaudio
import wave
import os
import time


class AudioThread(QThread):
    # 定义一个信号，参数为识别结果的类型，这里假设为str
    recognition_result_signal = pyqtSignal(str)
    begin_record_signal = pyqtSignal(str)
    end_record_signal = pyqtSignal(str)

    def __init__(self, app_id, api_key, secret_key):
        super().__init__()
        self._run_flag = True
        self.client = AipSpeech(app_id, api_key, secret_key)
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.record_seconds = 3  # 每次录音时长

    def run(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.audio_format, channels=self.channels,
                        rate=self.rate, input=True,
                        frames_per_buffer=self.chunk)

        while self._run_flag:
            # print("开始录音...")
            self.begin_record_signal.emit("开始录音")
            frames = []

            for i in range(0, int(self.rate / self.chunk * self.record_seconds)):
                data = stream.read(self.chunk)
                frames.append(data)

            # 停止录音
            # print("录音结束.")
            self.end_record_signal.emit("录音结束")

            # 保存录音文件
            wave_file_path = "temp.wav"
            wf = wave.open(wave_file_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()

            # 识别录音文件
            recognition_result = self.client.asr(self.get_file_content(wave_file_path), 'wav', self.rate, {
                'dev_pid': 1537,
            })

            # 发出识别结果信号
            if recognition_result and recognition_result['err_no'] == 0:
                text = recognition_result['result'][0]
                self.recognition_result_signal.emit(text)
                print("text:", text)
            else:
                print("识别失败:", recognition_result.get('err_msg', ''))

            # 删除临时录音文件
            os.remove(wave_file_path)

            # 简单的延时，避免CPU占用过高
            time.sleep(0.5)

        stream.stop_stream()
        stream.close()
        p.terminate()
    
    def start(self):
        self._run_flag = True
        # 执行父类start函数
        super().start()

    def stop(self):
        self._run_flag = False
        self.wait()

    @staticmethod
    def get_file_content(filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

