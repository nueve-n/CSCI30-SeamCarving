#!/usr/bin/env python3

from PIL import Image


class Picture(dict):
    def __init__(self, img: Image.Image):
        '''
        Takes a PIL image, and stores pixels in its dictionary
        '''
        img = img.convert('RGB')
        self._width, self._height = img.size
        pixels = iter(img.getdata())
        for j in range(self._height):
            for i in range(self._width):
                self[i, j] = next(pixels)

    def picture(self) -> Image.Image:
        '''
        Get the current picture represented by self
        '''
        picture = Image.new('RGB', (self._width, self._height))
        picture.putdata([self[i, j] for j in range(self._height) for i in range(self._width)])
        return picture

    def width(self) -> int:
        '''
        Return the width of current picture
        '''
        return self._width

    def height(self) -> int:
        '''
        Return the height of current picture
        '''
        return self._height

    def show(self):
        self.picture().show()

    def color_seam(self, seam: list[int], vertical=True, color=(255, 0, 255)):
        for i, j in enumerate(seam):
            if vertical:
                self[j, i] = color
            else:
                self[i, j] = color
