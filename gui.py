#!/usr/bin/env python3
'''
A graphical front end for your seam carver.  ou do not need to modify (or
submit) this file.

    python gui.py                 open an empty window
    python gui.py data/boat.jpg   open a picture straight away

All the work (finding and removing seams) happens in a background thread,
so the window stays responsive while your code runs. If your code raises an
exception, the message appears at the bottom of the window and the full
traceback in the terminal.
'''

import os
import sys
import time
import traceback

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QRadioButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from seamcarver import SeamCarver

SEAM_COLOR = (255, 0, 255)
MIN_WIDTH, MIN_HEIGHT = 540, 150


def to_pixmap(image: Image.Image) -> QPixmap:
    '''Convert a PIL image to a QPixmap (call this in the GUI thread only).'''
    image = image.convert('RGB')
    data = image.tobytes('raw', 'RGB')
    qimage = QImage(data, image.width, image.height, 3 * image.width,
                    QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimage.copy())    # copy: `data` is about to go away


def render(carver, seam=None, vertical=True) -> Image.Image:
    '''
    Draw the carver's current picture, with a seam in pink if given.

    The seam is painted on a copy: the SeamCarver itself is never modified,
    so saving the picture afterwards does not save the seam.
    '''
    image = carver.picture()
    if seam is not None:
        for k, x in enumerate(seam):
            image.putpixel((x, k) if vertical else (k, x), SEAM_COLOR)
    return image


class Signals(QObject):
    frame = Signal(object)          # a PIL image to display
    status = Signal(str)
    seam = Signal(object)           # the seam just found, or None
    repeat = Signal(int)            # seams still to remove
    failed = Signal(str)
    finished = Signal()


class Task(QRunnable):
    '''Run job(signals) in a worker thread, reporting any exception.'''

    def __init__(self, job):
        super().__init__()
        self.job = job
        self.signals = Signals()

    @Slot()
    def run(self):
        try:
            self.job(self.signals)
        except Exception as exc:
            traceback.print_exc()
            self.signals.failed.emit(f'{type(exc).__name__}: {exc}'.rstrip(': '))
        finally:
            self.signals.finished.emit()


class SeamCarverGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.carver = None          # the SeamCarver being edited
        self.seam = None            # a seam found but not yet removed
        self.vertical = True

        self.setWindowTitle('CSCI 30 Seam Carving')
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.buttons = QGridLayout()
        open_button = QPushButton('Open image')
        open_button.clicked.connect(self.open_image)
        self.buttons.addWidget(open_button, 0, 0)
        self.save_button = QPushButton('Save image')
        self.save_button.clicked.connect(self.save_image)
        self.buttons.addWidget(self.save_button, 1, 0)

        self.show_seam_button = QPushButton('Show seam')
        self.show_seam_button.clicked.connect(self.show_seam)
        self.buttons.addWidget(self.show_seam_button, 0, 1)
        self.remove_seam_button = QPushButton('Remove seam')
        self.remove_seam_button.clicked.connect(self.remove_seam)
        self.buttons.addWidget(self.remove_seam_button, 1, 1)

        orientation = QHBoxLayout()
        orientation.addWidget(QLabel('Seam:'))
        self.toggle_v = QRadioButton('&Vertical', self)
        self.toggle_v.setChecked(True)
        self.toggle_v.toggled.connect(self.toggle_orientation)
        orientation.addWidget(self.toggle_v)
        self.toggle_h = QRadioButton('&Horizontal', self)
        orientation.addWidget(self.toggle_h)
        self.buttons.addLayout(orientation, 0, 2)

        repeat = QHBoxLayout()
        repeat.addWidget(QLabel('Repeat:'))
        self.repeat = QSpinBox()
        self.repeat.setRange(1, 100)
        repeat.addWidget(self.repeat)
        self.buttons.addLayout(repeat, 1, 2)

        self.view = QLabel()
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.view)
        self.scroll.setWidgetResizable(False)
        self.scroll.hide()

        self.status = QLabel('Please open an image.')
        self.status.setWordWrap(True)

        layout.addLayout(self.buttons)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(self.status)
        self.set_busy(False)
        self.resize(MIN_WIDTH, MIN_HEIGHT)

    # opening and saving

    def open_image(self, fname=None):
        if not fname:
            fname = QFileDialog.getOpenFileName(
                self, 'Open image', '.', 'Image files (*.jpg *.jpeg *.png)')[0]
        if not fname:
            return
        name = os.path.basename(fname)
        self.update_status(f'Loading {name}...')
        try:
            self.carver = SeamCarver(Image.open(fname).convert('RGB'))
        except Exception as exc:
            traceback.print_exc()
            self.update_status(f'Error loading {name}: {exc}')
            return
        self.seam = None
        self.show_frame(render(self.carver))
        self.update_status(f'Loaded {name} ({self.carver.width()}x{self.carver.height()}). '
                           'Now show or remove a seam.')
        self.set_busy(False)

    def save_image(self):
        if self.carver is None:
            return
        fname = QFileDialog.getSaveFileName(
            self, 'Save image', '.', 'Image files (*.jpg *.jpeg *.png)')[0]
        if not fname:
            return
        name = os.path.basename(fname)
        try:
            self.carver.picture().save(fname)
        except Exception as exc:
            traceback.print_exc()
            self.update_status(f'Error saving {name}: {exc}')
            return
        self.update_status(f'Saved {name}.')

    # seams

    def find_seam(self, signals, count=0):
        '''Return the pending seam, finding one first if necessary.'''
        if self.seam is None:
            kind = 'vertical' if self.vertical else 'horizontal'
            label = f' {count + 1}' if count else ''
            signals.status.emit(f'Computing {kind} seam{label}...')
            if self.vertical:
                self.seam = self.carver.find_vertical_seam()
            else:
                self.seam = self.carver.find_horizontal_seam()
        return self.seam

    def show_seam(self):
        if self.carver is None:
            return

        def job(signals):
            seam = self.find_seam(signals)
            signals.frame.emit(render(self.carver, seam, self.vertical))
            kind = 'vertical' if self.vertical else 'horizontal'
            signals.status.emit(f'Computed {kind} seam, as shown in pink.')

        self.start(job)

    def remove_seam(self):
        if self.carver is None:
            return
        reps = self.repeat.value()

        def job(signals):
            for count in range(reps):
                seam = self.find_seam(signals, count)
                signals.frame.emit(render(self.carver, seam, self.vertical))
                time.sleep(0.1)
                if self.vertical:
                    self.carver.remove_vertical_seam(seam)
                else:
                    self.carver.remove_horizontal_seam(seam)
                self.seam = None
                signals.frame.emit(render(self.carver))
                signals.repeat.emit(max(reps - count - 1, 1))
            size = f'{self.carver.width()}x{self.carver.height()}'
            signals.status.emit(f'Removed {reps} seams; now {size}.' if reps > 1
                                else f'Removed seam; now {size}.')

        self.start(job)

    def start(self, job):
        task = Task(job)
        task.signals.frame.connect(self.show_frame)
        task.signals.status.connect(self.update_status)
        task.signals.repeat.connect(self.repeat.setValue)
        task.signals.failed.connect(self.report_failure)
        task.signals.finished.connect(self.task_finished)
        self.set_busy(True)
        self.threadpool.start(task)

    def task_finished(self):
        self.set_busy(False)

    def report_failure(self, message):
        self.seam = None
        self.update_status(f'Error: {message} (traceback in the terminal)')
        if self.carver is not None:
            try:
                self.show_frame(render(self.carver))
            except Exception:
                traceback.print_exc()

    def toggle_orientation(self):
        self.vertical = self.toggle_v.isChecked()
        if self.seam is not None:       # the seam on display is for the other direction
            self.seam = None
            self.show_frame(render(self.carver))

    # display

    def set_busy(self, busy):
        ready = self.carver is not None and not busy
        for widget in (self.show_seam_button, self.remove_seam_button, self.save_button,
                       self.toggle_v, self.toggle_h, self.repeat):
            widget.setEnabled(ready)

    def show_frame(self, image):
        pixmap = to_pixmap(image)
        self.view.setPixmap(pixmap)
        self.view.resize(pixmap.size())
        if self.scroll.isHidden():
            self.scroll.show()
            self.centralWidget().layout().activate()
        # Grow or shrink the window so the picture just fits, within the screen.
        viewport = self.scroll.viewport().size()
        extra_w, extra_h = self.width() - viewport.width(), self.height() - viewport.height()
        screen = self.screen().availableGeometry()
        width = min(max(pixmap.width() + extra_w, MIN_WIDTH), int(screen.width() * 0.95))
        height = min(max(pixmap.height() + extra_h, MIN_HEIGHT), int(screen.height() * 0.9))
        self.resize(width, height)

    def update_status(self, message):
        self.status.setText(message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SeamCarverGui()
    window.show()
    if len(sys.argv) > 1:
        window.open_image(sys.argv[1])
    sys.exit(app.exec())
