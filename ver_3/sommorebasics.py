from PyQt5.QtWidgets import *

def ifClicked():
    print("Clicked")

def ifClicked2():
    print("Other clicked")

app = QApplication([])
window = QMainWindow()

centerWidget = QWidget()

button = QPushButton('Test', centerWidget)
button2 = QPushButton('Test2', centerWidget)
button.setGeometry(0,50,120,40)
button.clicked.connect(ifClicked)
button2.clicked.connect(ifClicked2)

window.setCentralWidget(centerWidget)
window.setWindowTitle('mainwindow')
window.show()

app.exit(app.exec_())