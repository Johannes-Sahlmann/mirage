"""System test of mirage/NIRISS that creates simulations based on a .yaml file.

Authors
-------
    - Johannes Sahlmann

Use
---
    >>> pytest -s test_niriss_imaging.py


"""

import os

from mirage.scripts import imaging_simulator as im

# os.environ['MIRAGE_DATA'] = ''
os.environ['TEST_DATA'] = os.path.join(os.path.dirname(__file__), 'test_data/NIRISS')

def test_niriss_imaging():
    m = im.ImgSim()
    m.paramfile = os.path.join(os.path.dirname(__file__), 'test_data/NIRISS/niriss_imaging_example.yaml')
    m.create()
