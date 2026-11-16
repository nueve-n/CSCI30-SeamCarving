#!/usr/bin/env python3

from picture import Picture

class SeamCarver(Picture):
    ## TO-DO: fill in the methods below
    def energy(self, i: int, j: int) -> float:
        '''
        Return the energy of pixel at column i and row j

        Milestone 1 (pytest -m m1)
        '''
        raise NotImplementedError

    def find_vertical_seam(self) -> list[int]:
        '''
        Return a sequence of indices representing the lowest-energy
        vertical seam

        Milestone 2 (pytest -m m2)
        '''
        raise NotImplementedError

    def find_horizontal_seam(self) -> list[int]:
        '''
        Return a sequence of indices representing the lowest-energy
        horizontal seam

        Milestone 3 (pytest -m m3)
        '''
        raise NotImplementedError

    def remove_vertical_seam(self, seam: list[int]):
        '''
        Remove a vertical seam from the picture

        Milestone 4 (pytest -m m4)
        '''
        raise NotImplementedError

    def remove_horizontal_seam(self, seam: list[int]):
        '''
        Remove a horizontal seam from the picture

        Milestone 5 (pytest -m m5)
        '''
        raise NotImplementedError

class SeamError(Exception):
    pass
