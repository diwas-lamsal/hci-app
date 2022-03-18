import sys
from PyQt5.QtWidgets import QApplication
from mediaplayer import Window


app = QApplication(sys.argv)

window = Window()
window.show()

sys.exit(app.exec())
