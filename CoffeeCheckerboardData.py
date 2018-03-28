from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

# noinspection PyUnresolvedReferences
from builtins import *

import os
import logging
from glob import glob
from astropy.io import fits

from hicat.hicat_types import MetaDataEntry

from .Experiment import Experiment
from ..hardware.boston.commands import checkerboard_command, flat_command
from ..hardware import testbed
from ..config import CONFIG_INI
from .. import util
from ..hicat_types import units, quantity, FpmPosition, ImageCentering
from .modules.general import take_exposures, take_coffee_data_set


class CoffeeCheckerboardData(Experiment):
    name = "Coffee Checkerboard Data"
    log = logging.getLogger(__name__)

    def __init__(self,
                 amplitude=quantity(800, units.nanometer),
                 direct_exp_time=quantity(250, units.microsecond),
                 coron_exp_time=quantity(1, units.millisecond),
                 num_exposures=10,
                 path=None,
                 camera_type="imaging_camera",
                 focus_zernike_data_path="z:/Testbeds/hicat_dev/data_vault/dm2_calibration/2018-01-21T09-34-00_4d_zernike_loop_focus/",
                 centering=ImageCentering.custom_apodizer_spots,
                 **kwargs):

        self.amplitude = amplitude
        self.direct_exp_time = direct_exp_time
        self.coron_exp_time = coron_exp_time
        self.num_exposures = num_exposures
        self.path = path
        self.camera_type = camera_type
        self.focus_zernike_data_path = focus_zernike_data_path
        self.centering = centering
        self.kwargs = kwargs

    def experiment(self):

        if self.path is None:
            central_store_path = CONFIG_INI.get("optics_lab", "local_data_path")
            self.path = util.create_data_path(initial_path=central_store_path,
                                              suffix="checkerboard_" + self.camera_type)
        dm_num = 1
        flat_dm_command = flat_command(bias=False, flat_map=True)

        # Generate the 16 permutations of checkerboards, and add the commands to a list.
        for i in range(0, 4):
            for j in range(0, 4):
                file_name = "checkerboard_{}_{}_{}nm".format(i, j, self.amplitude.m)
                command = checkerboard_command(dm_num=dm_num, offset_x=i, offset_y=j,
                                               amplitude=self.amplitude,
                                               bias=False, flat_map=True)

                # Create metadata.
                metadata = [MetaDataEntry("offset_x", "offset_x", i, "Checkerboard offset x-axis")]
                metadata.append(MetaDataEntry("offset_y", "offset_y", j, "Checkerboard offset y-axis"))
                metadata.append(MetaDataEntry("amplitude",
                                              "amp",
                                              self.amplitude.to(units.nanometer).m,
                                              "Amplitude in nanometers"))

                # # Pure Focus Zernike loop.
                focus_zernike_command_paths = glob(self.focus_zernike_data_path + "/*p2v/*.fits")
                take_coffee_data_set(focus_zernike_command_paths,
                                     self.path,
                                     file_name,
                                     self.coron_exp_time,
                                     self.direct_exp_time,
                                     dm1_command_object=command,
                                     num_exposures=self.num_exposures,
                                     centering=self.centering,
                                     extra_metadata=metadata)


