from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from builtins import *

from hicat.interfaces.Camera import Camera
from hicat.config import CONFIG_INI
from hicat import units, quantity
from hicat.hardware import testbed_state
from astropy.io import fits
from PIL import Image
from io import BytesIO
from time import sleep
import numpy as np
import os
import requests
import sys

# implementation of a camera to run the SBIG STX-16803 Pupil Cam and KAF-1603ME/STT-1603M small cam

class SbigCamera(Camera):

    FRAME_TYPE_DARK=0
    FRAME_TYPE_LIGHT=1
    FRAME_TYPE_BIAS=2
    FRAME_TYPE_FLAT_FIELD=3

    IMAGER_STATE_IDLE=0
    IMAGER_STATE_EXPOSING=2
    IMAGER_STATE_READING_OUT=3
    IMAGER_STATE_ERROR=5

    NO_IMAGE_AVAILABLE=0
    IMAGE_AVAILABLE=1

    def initialize(self, *args, **kwargs):
        """Loads the SBIG config information and verifies that the camera is idle.
           Uses the config_id to look up parameters in the config.ini"""

        # find the SBIG config information
        camera_name = CONFIG_INI.get(self.config_id, "camera_name")
        self.base_url = CONFIG_INI.get(self.config_id, "base_url")
        self.timeout = CONFIG_INI.getint(self.config_id, "timeout")
        self.min_delay = CONFIG_INI.getfloat(self.config_id, 'min_delay')

        # check the status, which should be idle
        imager_status = self.__check_imager_state()
        if imager_status > self.IMAGER_STATE_IDLE:
            # Error.  Can't start the camera or camera is already busy
            raise Exception("Camera reported incorrect state (" + str(imager_status) + ") during initialization.")

        self.imager_status = imager_status



    def close(self):
        # check status and abort any imaging in progress
        imager_status = self.__check_imager_state()
        if imager_status > self.IMAGER_STATE_IDLE:
            # work in progress, abort the exposure
            sleep(self.min_delay) # limit the rate at which requests go to the camera
            r = requests.get(self.base_url + "ImagerAbortExposure.cgi")
            # no data is returned, but an http error indicates if the abort failed
            r.raise_for_status()

    def take_exposures(self, exposure_time, num_exposures, path="", filename="",
                       fits_header_dict=None, center_x=None, center_y=None, width=None, height=None,
                       gain=None, full_image=None, bins=None, resume=False, write_out_data=True):
        if write_out_data:
            self.take_exposures_fits(exposure_time, num_exposures, path, filename,
                                     fits_header_dict, center_x, center_y, width, height,
                                     gain, full_image, bins, resume)
            return

        else:
            img_list = self.take_exposures_data(exposure_time, num_exposures,
                                                center_x, center_y, width, height,
                                                gain, full_image, bins)
            return img_list

    def take_exposures_fits(self, exposure_time, num_exposures, path, filename,
                                fits_header_dict=None, center_x=None, center_y=None, width=None, height=None,
                                gain=None, full_image=None, bins=None, resume=False):
            """
            Takes exposures, saves as FITS files and returns list of file paths. The keyword arguments
            are used as overrides to the default values stored in config.ini.
            :param exposure_time: Pint quantity for exposure time, otherwise in seconds.
            :param num_exposures: Number of exposures.
            :param path: Path of the directory to save fits file to.
            :param filename: Name for file.
            :param fits_header_dict: Dictionary of extra attributes to stuff into fits header.
            :param center_x: X coordinate of center pixel.
            :param center_y: Y coordinate of center pixel.
            :param width: Desired width of image.
            :param height: Desired height of image.
            :param gain: Gain of ZWO camera (volts).
            :param full_image: Boolean for whether to take a full image.
            :param bins: Integer value for number of bins.
            :param resume: If True, will skip exposure if image exists on disk already.
            :return: List of file paths to the fits files created.
            """

            # Convert exposure time to contain units if not already a Pint quantity.
            if type(exposure_time) is not quantity:
                exposure_time = quantity(exposure_time, units.seconds)

            self.__setup_control_values(exposure_time, center_x=center_x, center_y=center_y, width=width,
                                        height=height, gain=gain, full_image=full_image, bins=bins)

            # Check for fits extension.
            if not (filename.endswith(".fit") or filename.endswith(".fits")):
                filename += ".fits"

            # Split the filename once here, code below may append _frame=xxx to basename.
            file_split = os.path.splitext(filename)
            file_root = file_split[0]
            file_ext = file_split[1]

            # Create directory if it doesn't exist.
            if not os.path.exists(path):
                os.makedirs(path)

            filepath_list = []

            # Take exposure. Use Astropy to handle fits format.
            # Does not use the SBIG Imager Data FITS API
            for i in range(num_exposures):

                # For multiple exposures append frame number to end of base file name.
                if num_exposures > 1:
                    filename = file_root + "_frame" + str(i + 1) + file_ext
                full_path = os.path.join(path, filename)

                # If Resume is enabled, continue if the file already exists on disk.
                if resume and os.path.isfile(full_path):
                    print("File already exists: " + full_path)
                    continue

                img = self.__take_single_image(exposure_time)
                # Create a PrimaryHDU object to encapsulate the data.
                hdu = fits.PrimaryHDU(img)

                # Add headers.
                hdu.header["EXP_TIME"] = (exposure_time.to(units.microseconds).magnitude, "microseconds")
                hdu.header["CAMERA"] = (self.config_id, "Model of camera, correlates to entry in ini")
                hdu.header["GAIN"] = self.gain
                hdu.header["BINS"] = self.bins
                hdu.header["FRAME"] = i + 1
                hdu.header["FILENAME"] = filename

                # Add testbed state metadata.
                for entry in testbed_state.create_metadata():
                    if len(entry.name_8chars) > 8:
                        print("Fits Header Keyword: " + entry.name_8chars +
                              " is greater than 8 characters and will be truncated.")
                    if len(entry.comment) > 47:
                        print("Fits Header comment for " + entry.name_8chars +
                              " is greater than 47 characters and will be truncated.")
                    hdu.header[entry.name_8chars[:8]] = (entry.value, entry.comment)

                # Add extra header keywords passed in.
                if fits_header_dict:
                    for k, v in fits_header_dict.items():
                        if len(k) > 8:
                            print("Fits Header Keyword: " + k + " is greater than 8 characters and will be truncated.")
                        hdu.header[k[:8]] = v

                # Create a HDUList to contain the newly created primary HDU, and write to a new file.
                fits.HDUList([hdu])
                hdu.writeto(full_path, overwrite=True)
                print("wrote " + full_path)
                filepath_list.append(full_path)

            return filepath_list

    def take_exposures_data(self, exposure_time, num_exposures,
                            center_x=None, center_y=None, width=None, height=None,
                            gain=None, full_image=None, bins=None):
        """Takes exposures and returns list of numpy arrays."""

        # Convert exposure time to contain units if not already a Pint quantity.
        if type(exposure_time) is not quantity:
            exposure_time = quantity(exposure_time, units.microsecond)

        self.__setup_control_values(exposure_time, center_x=center_x, center_y=center_y, width=width,
                                    height=height, gain=gain, full_image=full_image, bins=bins)
        img_list = []

        # Take exposures and add to list.
        for i in range(num_exposures):
            img = self.__take_single_image(exposure_time)
            img_list.append(img)

        return img_list

    def __setup_control_values(self, exposure_time, center_x=None, center_y=None, width=None, height=None,
                               gain=None, full_image=None, bins=None):
        """Applies control values found in the config.ini unless overrides are passed in, and does error checking.
           Makes HTTP requests to set the imager settings.  Will raise an exception for an HTTP error."""

        # Load values from config.ini into variables, and override with keyword args when applicable.
        self.center_x = center_x if center_x is not None else CONFIG_INI.getint(self.config_id, 'center_x')
        self.center_y = center_y if center_y is not None else CONFIG_INI.getint(self.config_id, 'center_y')
        self.width = width if width is not None else CONFIG_INI.getint(self.config_id, 'width')
        self.height = height if height is not None else CONFIG_INI.getint(self.config_id, 'height')
        self.gain = gain if gain is not None else CONFIG_INI.getint(self.config_id, 'gain')
        self.full_image = full_image if full_image is not None else CONFIG_INI.getboolean(self.config_id, 'full_image')
        self.bins = bins if bins is not None else CONFIG_INI.getint(self.config_id, 'bins')
        self.exposure_time = exposure_time if exposure_time is not None else CONFIG_INI.getfloat(self.config_id, 'exposure_time')

        # Store the camera's detector shape.
        detector_max_x = CONFIG_INI.getint(self.config_id, 'detector_width')
        detector_max_y = CONFIG_INI.getint(self.config_id, 'detector_length')

        if full_image:
            print("Taking full", detector_max_x, "x", detector_max_y, "image, ignoring region of interest params.")
            return

        # Check for errors, print them all out before exiting.
        error_flag = False

        # Check that width and height are multiples of 8
        if self.width % 8 != 0:
            print("Width is not a multiple of 8:", self.width)
            error_flag = True
        if self.height % 8 != 0:
            print("Height is not a multiple of 8:", self.height)
            error_flag = True

        # Convert to binned units
        if self.bins != 1:
            # For debugging
            # print("Converting to binned units: bins =", bins)

            self.center_x //= self.bins
            self.center_y //= self.bins
            self.width //= self.bins
            self.height //= self.bins
            # set the parameters for binning
            bin_params = {'BinX': str(self.bins), 'BinY': str(self.bins)}
            r = requests.get(self.base_url + "ImagerSetSettings.cgi", params=bin_params, timeout=self.timeout)
            r.raise_for_status()

        # Derive the start x/y position of the region of interest, and check that it falls on the detector.
        derived_start_x = self.center_x - (self.width // 2)
        derived_start_y = self.center_y - (self.height // 2)
        derived_end_x = self.center_x + (self.width // 2)
        derived_end_y = self.center_y + (self.height // 2)

        if derived_start_x > detector_max_x or derived_start_x < 0:
            print("Derived start x coordinate is off the detector ( max", detector_max_x - 1, "):", derived_start_x)
            error_flag = True

        if derived_start_y > detector_max_y or derived_start_y < 0:
            print("Derived start y coordinate is off the detector ( max", detector_max_y - 1, "):", derived_start_y)
            error_flag = True

        if derived_end_x > detector_max_x or derived_end_x < 0:
            print("Derived end x coordinate is off the detector ( max", detector_max_x - 1, "):", derived_end_x)
            error_flag = True

        if derived_end_y > detector_max_y or derived_end_y < 0:
            print("Derived end y coordinate is off the detector ( max", detector_max_y - 1, "):", derived_end_y)
            error_flag = True

        if full_image:
            print("Taking full", detector_max_x, "x", detector_max_y, "image, ignoring region of interest params.")
            fi_params = {'StartX': '0', 'StartY': '0',
                         'NumX': str(detector_max_x), 'NumY': str(detector_max_y),
                         'CoolerState': '0'}
            r = requests.get(self.base_url + "ImagerSetSettings.cgi", params=fi_params, timeout=self.timeout)
            r.raise_for_status()
        else:
            if error_flag:
                sys.exit("Exiting. Correct errors in the config.ini file or input parameters.")

        # Set Region of Interest.
        if not full_image:
            roi_params = {'StartX': str(derived_start_x), 'StartY': str(derived_start_y),
                         'NumX': str(width), 'NumY': str(height),
                         'CoolerState': '0'}
            r = requests.get(self.base_url + "ImagerSetSettings.cgi", params=roi_params, timeout=self.timeout)
            r.raise_for_status()


    def __check_imager_state(self):
        """Utility function to get the current state of the camera.
           Make an HTTP request and check for good response, then return the value of the response.
           Will raise an exception on an HTTP failure."""
        r = requests.get(self.base_url + "ImagerState.cgi", timeout=self.timeout)
        r.raise_for_status()
        return int(r.text)

    def __check_image_status(self):
        """Utility function to check that the camera is ready to expose.
           Make an HTTP request and check for good response, then return the value of hte response.
           Will raise an exception on an HTTP failure."""
        r = requests.get(self.base_url + "ImagerImageReady.cgi", timeout=self.timeout)
        r.raise_for_status()
        return int(r.text)

    def __take_single_image(self, exposure_time):
        """Utility function to start and exposure and wait until the camera has completed the
           exposure.  Then wait for the image to be ready for download, and download it.
           Assumes the parameters for the exposure are already set."""

        # start an exposure.
        r = requests.get(self.base_url + "ImagerStartExposure.cgi",
                         data={'Duration': exposure_time.to(units.second).magnitude,
                               'FrameType': self.FRAME_TYPE_LIGHT},
                         timeout=self.timeout)
        r.raise_for_status()
        imager_state = self.IMAGER_STATE_EXPOSING

        # wait until imager has taken an image
        while imager_state > self.IMAGER_STATE_IDLE:
            sleep(self.min_delay)  # limit the rate at which requests go to the camera
            imager_state = self.__check_imager_state()
            if imager_state > self.IMAGER_STATE_EXPOSING:
                # an error has occurred
                print('Imager error during exposure')
                raise Exception("Camera reported error during exposure.")

        # at loop exit, the image should be available
        image_state = self.__check_imager_state()
        if image_state <> self.IMAGE_AVAILABLE:
            print('No image after exposure')
            raise Exception("Camera reported no image available after exposure.")

        # get the image
        r = requests.get(self.base_url + "ImagerData.bin", timeout=self.timeout)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)) # need to test if this gets the whole image or we need to loop while imager data is available
        return img
