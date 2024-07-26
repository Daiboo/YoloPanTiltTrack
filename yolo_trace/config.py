# load custom plugin and engine
PLUGIN_LIBRARY = "build/libmyplugins.so"

# 这里是的你的模型的路径
engine_file_path = "build/best.engine"

# 这里是你的目标检测的类别,注意顺序要和你的模型训练时的顺序一致
categories = ["box", "cup", "glue-stick", "phone"
            ]


# 这里要放你的百度api
APP_ID = ""
API_KEY = ''
SECRET_KEY = ''