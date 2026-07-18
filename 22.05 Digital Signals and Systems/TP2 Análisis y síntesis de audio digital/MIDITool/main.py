import logging.config
import sys
from typing import NoReturn
import app


def main() -> NoReturn:
    logging.config.fileConfig("./logging.ini")
    aplicacion = app.QtWidgets.QApplication(sys.argv)
    ventana = app.MainWindow()
    ventana.show()
    sys.exit(aplicacion.exec())


if __name__ == "__main__":
    main()
