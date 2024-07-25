import sys
from PyQt5.QtWidgets import QApplication, QWidget


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = QWidget()
	window.setWindowTitle('PyQt5安装测试')
	window.show()
	sys.exit(app.exec_())