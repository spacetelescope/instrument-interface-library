"""
Holds the class SegmentedDmCommand that is used to create a dict that will be sent to the
segmented DM hardware as a command.


This module can be used to create a command in the following way:
    poppy_obj = PoppySegmentedCommand(global_coefficients, dm_config_id, wavelength)
    command = poppy_obj.to_dm_list()
    iris_command = segmented_dm_command.load_command(command, dm_config_id,
                                                     wavelength,
                                                     testbed_config_id,
                                                     apply_flat_map=True,
                                                     filename_flat=FLAT_COMMAND_FILE)
    iris_command.display()

Note that a command can be zeros, None, a poppy command, a .ini file, or a .PTT### file.
Additionally, a single segment can be changed using the SegmentedDmCommand.update_one_segment()
method.

"""
from configparser import NoOptionError
import json
import os

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import poppy

from catkit.catkit_types import MetaDataEntry
from catkit.config import CONFIG_INI
from catkit.hardware.iris_ao import util


class SegmentedAperture:
    """
    Create a segmented aperture with Poppy using the parameters for the testbed
    and segmented DM from the config.ini file.

    To create an aperture, with the config.ini file loaded, run:
        segmented_aperture_obj = SegmentedAperture()
        my_aperture = segmented_aperture_obj.create_aperture()

    :param dm_config_id: str, name of the section in the config_ini file where information
                         regarding the segmented DM can be found.
    :param wavelength: float, wavelength in nm of the poppy optical system used for
                        (extremely oversimplified) focal plane simulations
    :attribute wavelength: float, wavelength in nm of the poppy optical system
    :attribute outer_ring_corners: bool, whether or not the segmented aperture includes
                                   the corner segments on the outer-most ring. If True,
                                   corner segments are included. If False, they are not
    :attribute center_segment: bool, whether of not the segmented aperture includes the
                               center segment. If True, the center segment is included.
                               If False, it is not.
    :attribute flat_to_flat: float, physical distance from flat to flat side of a DM segment
                             in units of mm
    :attribute gap: float, physical distance between DM segments in units of microns
    :attribute number_segments_in_pupil: int, number of segments included in the aperture for active
                                         control as specified by the "active_number_of_segments"
                                         parameter in the config file
    """

    def __init__(self, dm_config_id, wavelength):
        # Set config sections
        self.dm_config_id = dm_config_id

        # Parameters specific to testbed setup being used
        self.wavelength = wavelength * u.nm

        # Parameters specifc to the aperture and segmented DM being used
        self.outer_ring_corners = CONFIG_INI.getboolean(self.dm_config_id, 'include_outer_ring_corners')
        self.center_segment = CONFIG_INI.getboolean(self.dm_config_id, 'include_center_segment')
        self.flat_to_flat = CONFIG_INI.getfloat(self.dm_config_id, 'flat_to_flat_mm') * u.mm
        self.gap = CONFIG_INI.getfloat(self.dm_config_id, 'gap_um') * u.micron
        self.number_segments_in_pupil = CONFIG_INI.getint(self.dm_config_id, 'active_number_of_segments')

        # Get the specific segments
        self._num_rings = self.get_number_of_rings_in_pupil()
        self._segment_list = self.get_segment_list()

        self.aperture = self.create_aperture()

    def create_aperture(self):
        """
        Based on values in config file, create the aperture to be simulated

        :return: A Poppy HexSegmentedDeformableMirror object for this aperture
        """
        aperture = poppy.dms.HexSegmentedDeformableMirror(name='Segmented DM',
                                                          rings=self._num_rings,
                                                          flattoflat=self.flat_to_flat,
                                                          gap=self.gap,
                                                          segmentlist=self._segment_list,
                                                          rotation=0)
        return aperture

    def get_number_of_rings_in_pupil(self):
        """
        Get the number of rings based on the number of active segments specified in the
        config.ini file.

        :return: num_rings: int, the number of full rings of hexagonal segments in the aperture
        """
        active_segs_per_ring = self.get_active_number_of_segments_per_ring()

        try:
            num_rings = active_segs_per_ring.index(self.number_segments_in_pupil)
        except ValueError as error:
            raise ValueError("Invalid number of segments. Please check your config.ini file.") from error

        return num_rings

    def get_active_number_of_segments_per_ring(self, max_number_of_rings=7):
        """
        Given pupil specifics, returns a list of length equal to the maximum
        number of rings where each element is the total number of segments in a
        pupil with that number of rings.

        Given the use of the center segment or outer ring corner segments,
        return a list of the number of total active segments in a pupil, of a variety
        of number of rings that is indicated by its index in the list. For example,
        the first element in the list, with index of 1, will give the total number of
        active segments in a pupil with 1 ring which include the center segment if that
        segment is active. Note: The maximum number of rings for the PTT489 from IrisAO is 7

        return: list of total number of active segments in a pupil for pupils with
                a number of rings as indicated by the index of in the list
        """
        max_number_segments_in_pupil_per_ring = self.get_max_number_segments_in_pupil_per_ring(max_number_of_rings)

        # If no outer corners, you will have 6 fewer segments in that outer ring
        if not self.outer_ring_corners:
            active_segments_in_pupil_per_ring = [num-6 if num > 6 else num for num in max_number_segments_in_pupil_per_ring]
        # If no center segment, you will have 1 fewer segment overall
        if not self.center_segment:
            active_segments_in_pupil_per_ring = [num-1 for num in max_number_segments_in_pupil_per_ring]

        if self.outer_ring_corners and self.center_segment:
            active_segments_in_pupil_per_ring = max_number_segments_in_pupil_per_ring

        return active_segments_in_pupil_per_ring

    def get_max_number_segments_in_pupil_per_ring(self, number_of_rings=7):
        """Returns a list of length equal to the maximum number of rings in a pupil
        with hexagonal segments where each element is the total number of segments in a
        pupil with that number of rings.

        :return: list, list of length equal to the total number of rings where each element
        is the total number of segments in a pupil with that number of rings.
        """
        max_number_segments_in_pupil_per_ring = [1,] # number of segments in the pupil per ring
        for i in np.arange(number_of_rings)+1:
            max_number_segments_in_pupil_per_ring.append(max_number_segments_in_pupil_per_ring[i-1]+i*6)

        return max_number_segments_in_pupil_per_ring

    def get_segment_list(self):
        """
        Grab the list of segments to be used in your pupil taking into account if your
        aperture has a center segment and/or the segments in the corners of the outer ring.
        This list is passed to Poppy to help create the aperture.

        :param num_rings: int, The number of rings in your pupil
        :return: list, the list of segments
        """
        num_segs = self.total_number_segments_in_aperture(self._num_rings)
        seglist = np.arange(num_segs)

        # If no outer corners, you will have 6 fewer segments in that outer ring
        if not self.outer_ring_corners:
            inner_segs = seglist[:(num_segs-6*self._num_rings)]
            outer_segs = seglist[(num_segs-6*self._num_rings):]
            outer_segs = np.delete(outer_segs, np.arange(0, outer_segs.size,
                                                         self._num_rings)) # delete corner segs
            seglist = np.concatenate((inner_segs, outer_segs))

        if not self.center_segment:
            seglist = seglist[1:]
        return seglist

    def total_number_segments_in_aperture(self, number_of_rings=7):
        """
        For a segmented aperture of rings = number_of_rings, give the total number of
        segments in the aperture given an aperture of 1, 2, 3, etc. rings. Will return
        a list of the total number of segments in the *aperture* per ring where the ring
        is indicated by the index in the list.

        param: number_of_rings, int, the number of rings in the aperture
        return: a list of segments where the index of the value corresponds to the
                 number of rings. For example: index 0 corresponds with the center
                 where there is one segment.
        """
        number_segments_in_pupil_per_ring = self.get_max_number_segments_in_pupil_per_ring(number_of_rings)

        return number_segments_in_pupil_per_ring[number_of_rings]


class SegmentedDmCommand(SegmentedAperture):
    """
    Handle segmented DM specific commands in terms of piston, tip and tilt (PTT) for
    each segment. Creates a dictionary of the form {seg: (piston, tip, tilt)} that can
    be loaded onto the hardware.

    Units of the loaded command are expected to be in um (for piston) and mrad (for tip and tilt)

    This class does NOT interact with hardware directly.

    :param apply_flat_map: If true, add flat map correction to the data before creating command
    :param filename_flat: string, full path to custom flat map
    :param dm_config_id: str, name of the section in the config_ini file where information
                         regarding the segmented DM can be found.
    :param wavelength: float, wavelength in nm of the poppy optical system used for
                        (extremely oversimplified) focal plane simulations
    :param testbed_config_id: str, name of the section in the config_ini file where information
                           regarding the testbed can be found.
    :attribute data: list of tuples, input data that can then be updated. This attribute never
                     never includes the flat map values.
    :attribute apply_flat_map: bool, whether or not to apply the flat map
    :attribute source_pupil_numbering: list, numbering native to data
    :attribute command: dict, final command with flat if apply_flat_map = True
    :attribute filename_flat: str, full path to custom flat
    :attribute total_number_segments: int, total number of segments in DM
    :attribute active_segment_list: int, number of active segments in the DM
    :attribute instrument_fov: int, field of view of the instrument
    :attribute pixelscale: float, pixelscale of the instrument
    :attribute dm_command_units: tuple of floats, the units of the piston, tip, tilt
                                 values on the hardware
    :attribute aperture: poppy.dms.HexSegmentedDeformableMirror object, the aperture
                         that you are defining
    """

    def __init__(self, dm_config_id, wavelength, testbed_config_id, apply_flat_map=False, filename_flat=''):
        # Initilize parent class used to create the aperture
        super().__init__(dm_config_id=dm_config_id, wavelength=wavelength)

        # Determine if the flat map will be applied
        self.apply_flat_map = apply_flat_map
        if self.apply_flat_map:
            self.filename_flat = filename_flat
            # Check that the file exists
            if not os.path.isfile(self.filename_flat):
                raise FileNotFoundError(f"{self.filename_flat} either does not exists or is not currently accessible")

        # Establish segment information
        try:
            self.segments_in_pupil = json.loads(CONFIG_INI.get(self.dm_config_id, 'active_segment_list'))
            if len(self.segments_in_pupil) != self.number_segments_in_pupil:
                raise ValueError("The length of active_segment_list does not match the active_number_of_segments in the config.ini. Please update your config.ini.")
        except NoOptionError:
            self.segments_in_pupil = util.iris_pupil_naming(self.dm_config_id)

        # Initalize parameters for displaying the command
        self.instrument_fov = CONFIG_INI.getint(testbed_config_id, 'fov_irisao_plotting')
        self.pixelscale = CONFIG_INI.getfloat(testbed_config_id, 'pixelscale_iriso_plotting')
        dm_command_units = CONFIG_INI.get(self.dm_config_id, 'dm_ptt_units').split(',')
        self.dm_command_units = [u.Unit(dm_command_units[0]), u.Unit(dm_command_units[1]),
                                 u.Unit(dm_command_units[2])]
        # Create the aperture
        self.aperture = self.create_aperture()

        # Initalize command
        self.data = util.create_zero_list(self.number_segments_in_pupil)
        self.input_data = None
        self.command = None

    def read_initial_command(self, segment_values):
        """
        Read a new command and assign to the attribute 'data'

        :param segment_values: str, list. Can be .PTT111, .ini files or a list with piston, tip,
                               tilt values in a tuple for each segment. See the load_command doc
                               string for more information.
        """
        self.input_data = self.data = self._read_command(segment_values)

    def _read_command(self, segment_values):
        """
        Read and return command from one of the allowed formats

        :param segment_values: str, list. Can be .PTT111, .ini files or a list with piston, tip,
                               tilt values in a tuple for each segment. See the load_command doc
                               string for more information.
        :return: list of tuples for each commanded segment
        """
        ptt_list, segment_names = util.read_segment_values(segment_values, self.dm_config_id)
        if segment_names is not None:
            command_list = []
            for seg_name in self.segments_in_pupil:  # Pull out only segments in the pupil
                ind = np.where(np.asarray(segment_names) == seg_name)[0][0]
                command_list.append(ptt_list[ind])
        else:
            command_list = ptt_list
        return command_list

    def get_data(self):
        """ Grab the current shape to be applied to the DM (does NOT include the flat map)
        """
        return self.data

    def to_command(self):
        """ Output command suitable (in the form a dictionary with an entry for each segment
        on the for sending to the hardware driver. The flat map will be added only at this stage
        """
        if self.apply_flat_map:
            command_data = self.add_map(self.filename_flat, return_new_map=True)
        else:
            command_data = self.data
        command_dict = dict(zip(self.segments_in_pupil, command_data))

        return command_dict

    def update_one_segment(self, segment_ind, ptt_tuple, add_to_current=True):
        """ Update the value of one segment by supplying the new command that will be added
        to or will replace the current PTT tuple. To identify the segment to be changed, give
        the *index* of that segment in the active segment list. This will be added
        to the current value only if the add_to_current flag is set to True, otherwise, value
        given will replace the current value.

        :param segment_ind: int, for the segment in the pupil that is to be updated,
                            provide the index of it's location in the active segment list
        :param ptt_tuple: tuple with three values for piston, tip, and tilt in um and mrad
        """
        if add_to_current:
            command_list = util.create_zero_list(self.number_segments_in_pupil)
            command_list[segment_ind] = ptt_tuple
            self.add_map(command_list)
        else:
            self.data[segment_ind] = ptt_tuple

    def add_map(self, segment_values_to_add, return_new_map=False):
        """
        Add a command to the one already loaded.

        :param new_command: str or list (.PTT111 or .ini file, or list, for example, from POPPY)
        """
        original_data = self.get_data()
        data_to_add = self._read_command(segment_values_to_add)

        new_map = [tuple(map(sum, zip(orig, addition))) for orig,
                   addition in zip(original_data, data_to_add)]

        if return_new_map:
            return new_map
        else:
            self.data = new_map

    def to_ini(self, filename, out_dir=''):
        """
        Write the command to a .ini file. Note: This will NOT include the applied flat
        map values
        :param filename: str, name of ini file to be written out
        :param out_dir: str, name of directory where ini file will be saved
        """
        data = self.get_data()
        command = dict(zip(self.segments_in_pupil, data))
        path = os.path.join(out_dir, filename)
        util.write_ini(command, path, dm_config_id=self.dm_config_id)

    def get_extra_meta_data(self):
        """
        Create meta data to be saved with fits files that gives the ptt values/segment
        and if the flat map was applied.The values saved will NOT include flat map PTT values.
        """
        metadata = []
        if self.apply_flat_map:
            metadata.append(MetaDataEntry("Flat Name", "FLATMAP", self.filename_flat,
                                          "Flat map name/file if applied"))
        rounded_ptt_list = round_ptt_list(self.data, decimals=4)
        for seg, ptt in zip(self.segments_in_pupil, rounded_ptt_list):
            metadata.append(MetaDataEntry(f"Segment {seg}", f"SEG{seg}", str(ptt),
                                          f"Piston/GradX/GradY applied for segment {seg}"))
        return metadata

    def display(self, display_wavefront=True, display_psf=True, psf_rotation_angle=90.,
                save_figures=True, figure_name_prefix='', out_dir=''):
        """
        Display either the deployed mirror state ("wavefront") and/or the PSF created
        by this mirror state.

        :param display_wavefront: bool, If true, display the deployed mirror state
        :param display_psf: bool, If true, display the simulated PSF created by the
            mirror state
        :param psf_rotation_angle: int/float, Degree value by which to rotate the simulated
            PSF in order to match your output
        :param figure_name_prefix: str, String to be added to filenames of output figures
        :param out_dir: str, name of output directory
        :param save_figures: bool, If true, save out the figures in the directory specified
                             by out_dir
        """
        # Grab the units of the DM for the piston, tip, tilt values and check that
        #  they don't exceed the DM hardware limits
        display_data = set_to_dm_limits(self.data)
        # Convert the PTT list from DM to Poppy units
        converted_list = convert_ptt_units(display_data, tip_factor=1, tilt_factor=-1,
                                           starting_units=self.dm_command_units,
                                           ending_units=(u.m, u.rad, u.rad))
        #rounded_list = round_ptt_list(converted_list, decimals=4)
        rounded_list = converted_list
        for seg, values in zip(self.aperture.segmentlist, rounded_list):
            self.aperture.set_actuator(seg, values[0], values[1], values[2])

        if figure_name_prefix:
            figure_name_prefix = f'{figure_name_prefix}_'
        if display_wavefront:
            self.plot_wavefront(figure_name_prefix, out_dir, save_figure=save_figures)
        if display_psf:
            self.plot_psf(psf_rotation_angle, figure_name_prefix, out_dir,
                          save_figure=save_figures)

    def plot_wavefront(self, figure_name_prefix, out_dir, vmax=0.5e-6*u.meter, save_figure=True):
        """
        Plot the deployed mirror state (wavefront error)

        :param figure_name_prefix: str, String to be added to filenames of output figures
        :param out_dir: str, name of output directory
        :param vmax: astropy unit quantity, the maximum value to display in the plot (as expected
                     by Poppy)
        :param save_figure: bool, If true, save out the figures in the directory specified by
                            out_dir
        """
        plt.figure()
        self.aperture.display(what='opd', title='Wavefront error applied to the active segments',
                              opd_vmax=vmax)
        if save_figure:
            plt.savefig(os.path.join(out_dir, f'{figure_name_prefix}wfe_on_dm.png'))
            plt.close()
        else:
            plt.show()

    def plot_psf(self, rotation_angle, figure_name_prefix, out_dir, vmin=10e-8,
                 vmax=10e-2, save_figure=True):
        """
        Plot the simulated PSF based on the mirror state

        :param rotation_anlge: float, the rotation to apply to the PSF image in order to match
                               our testbed. Note that this value is specific to each testbed
        :param figure_name_prefix: str, String to be added to filenames of output figures
        :param out_dir: str, name of output directory
        :param vmin: float, the minimum value to display in the plot
        :param vmax: float, the maximum value to display in the plot
        :param save_figure: bool, If true, save out the figures in the directory specified by
                            out_dir
        """
        plt.figure()
        osys = poppy.OpticalSystem()
        osys.add_pupil(self.aperture)
        osys.add_detector(pixelscale=self.pixelscale, fov_arcsec=self.instrument_fov)
        osys.add_rotation(angle=rotation_angle)

        psf = osys.calc_psf(wavelength=self.wavelength)
        poppy.display_psf(psf, vmin=vmin, vmax=vmax,
                          title='PSF created by the shape put on the active segments')
        if save_figure:
            plt.savefig(os.path.join(out_dir, f'{figure_name_prefix}simulated_psf.png'))
            plt.close()
        else:
            plt.show()


def load_command(segment_values, dm_config_id, wavelength, testbed_config_id,
                 apply_flat_map=True, filename_flat=''):
    """
    Loads the segment_values from a file or list and returns a SegmentedDmCommand object.

    There are only two allowed segment mappings for the input formats, Native and Centered Pupil.
    See the README for the Iris AO for more details.

    :param segment_values: str, list. Can be .PTT111, .ini files or a list with piston, tip,
                           tilt values in a tuple for each segment. For the list, the first
                           element is the center or top of the innermost ring of the pupil,
                           and subsequent elements continue up and/or clockwise around the
                           pupil (see README for more information)
    :param dm_config_id: str, name of the section in the config_ini file where information
                         regarding the segmented DM can be found.
    :param apply_flat_map: Apply a flat map in addition to the data.
    :param filename_flat: string, full path to the custom flat map
    :return: SegmentedDmCommand object representing the command dictionary.
    """
    dm_command_obj = SegmentedDmCommand(dm_config_id=dm_config_id, wavelength=wavelength,
                                        testbed_config_id=testbed_config_id,
                                        apply_flat_map=apply_flat_map,
                                        filename_flat=filename_flat)
    dm_command_obj.read_initial_command(segment_values)

    return dm_command_obj


## POPPY
def round_ptt_list(ptt_list, decimals=3):
    """
    Make sure that the PTT coefficients are rounded to a reasonable number of decimals

    :param ptt_list: list, of tuples existing of piston, tip, tilt, values for each
                     segment in a pupil
    :return: list of coefficients for piston, tip, and tilt, for your pupil rounded to
             the specified number of decimal places
    """
    return [(np.round(ptt[0], decimals), np.round(ptt[1], decimals),
             np.round(ptt[2], decimals)) for ptt in ptt_list]


def convert_ptt_units(ptt_list, tip_factor, tilt_factor, starting_units, ending_units):
    """
    Convert the PTT list to or from Poppy units and the segmented DM units.

    Note that this has been created for the IrisAO segmented DMs, therefore
    the tip and tilt values are swapped with what Poppy desginates.

    Poppy to segmented DM:
    - tip_factor = -1
    - tilt_facotr = 1
    - starting_units = (u.m, u.rad, u.rad)
    - ending_units = dm_ptt_units from the config.ini file

    Segmented DM to Poppy
    - tip_factor = 1
    - tilt_factor = -1
    - starting_units = dm_ptt_units from the config.ini file
    - ending_units = (u.m, u.rad, u.rad)

    :param ppt_list: list, of tuples existing of piston, tip, tilt, values for each
                     segment in a pupil
    :param tip_factor: int, either -1 or 1 based on the information above
    :param tilt_factor: int, either -1 or 1 based on the information above
    :param starting_units: tuple or list of the units associated with the piston, tip,
                           tilt values respectively of the input ptt_list
    :param ending_units: tuple_or_list of the units associated with the piston, tip,
                           tilt values respectively of the expected output
    :return: list of tuples of the piston, tip, tilt values for each segment listed
    """
    converted = [(ptt[0]*(starting_units[0]).to(ending_units[0]),
                  tip_factor*ptt[2]*(starting_units[2]).to(ending_units[2]),
                  tilt_factor*ptt[1]*(starting_units[1]).to(ending_units[1])) for ptt in ptt_list]
    return converted


def set_to_dm_limits(ptt_list, limit=5.):
    """
    Check that the values for piston, tip, and tilt are not exceeding the hardware
    limit and reset to limit if limit is exceeded. These limits are the same as what
    the IrisAO GUI has set.

    :param ppt_list: list, of tuples existing of piston, tip, tilt, values for each
                     segment in a pupil
    :param limit: float, in DM units. Default = 5.
    :return: list of tuples of the piston, tip, tilt values for each segment listed
             such that none of the values exceed the limit
    """
    updated = [tuple(min(i, limit) for i in ptt) for ptt in ptt_list]

    return updated


def get_wavefront_from_coeffs(coeff_list, basis):
    """
    Get the wavefront from the coefficients created by the basis given. This gives
    the per-segment wavefront based on the global coefficients given and the basis
    created.

    :params basis: POPPY Segment_PTT_Basis object, basis created that represents pupil
    :params coeff_list: list, per-segment list of piston, tip, tilt values for
                         the pupil described by basis
    :return wavefront, POPPY wavefront
    """
    wavefront = poppy.zernike.opd_from_zernikes(coeff_list, basis=basis)
    return wavefront


class PoppySegmentedCommand(SegmentedAperture):
    """
    Create a segement values list (and dictionary) (in POPPY: wavefront error) using
    POPPY for your pupil. This is currently limited to global shapes. The output is
    a list of piston, tip, tilt  values with units of (um, mrad, mrad), respectively,
    for each segment.

    This class inherits the SegmentedAperture class.

    To use to get command for the segmented DM:
      poppy_obj = PoppySegmentedCommand(global_coefficients)
      command = poppy_obj.to_dm_list()

    The method .to_dm_list() will place the command in the correct units and can then
    be used as input to load_command or be used with the DisplayCommand class.

    :param global_coefficients: list of global zernike coefficients in the form
                                [piston, tip, tilt, defocus, ...] (Noll convention)
                                in meters of optical path difference (not waves)
    :param dm_config_id: str, name of the section in the config_ini file where information
                         regarding the segmented DM can be found.
    :param wavelength: wavelength: float, wavelength in nm of the poppy optical system used for
                        (extremely oversimplified) focal plane simulations
    :attribute radius: float, half of the flat-to-flat distance of each segment
    :attribute num_terms: int, total number of PTT values on all segments (3 x number of segments)
    :attribute dm_command_units: list, the units of the piston, tip, tilt (respecitvely)
                                 values when coming from the DM or DM command
    :attribute global_coefficents: list of global zernike coefficients in the form
                                [piston, tip, tilt, defocus, ...] (Noll convention)
    :attribute basis: poppy.zernike.Segment_PTT_Basis object, basis based on the characteristics
                      of the segmented DM being used
    :attribute list of coefficients: list of piston, tip, tilt coefficients in units of u, rad, rad
    """
    def __init__(self, global_coefficients, dm_config_id, wavelength):
        # Initilize parent class
        super().__init__(dm_config_id=dm_config_id, wavelength=wavelength)

        self.radius = (self.flat_to_flat/2).to(u.m)
        self.num_terms = (self.number_segments_in_pupil) * 3

        # Grab the units of the DM for the piston, tip, tilt values to convert to
        dm_command_units = CONFIG_INI.get(self.dm_config_id, 'dm_ptt_units').split(',')
        self.dm_command_units = [u.Unit(dm_command_units[0]), u.Unit(dm_command_units[1]),
                                 u.Unit(dm_command_units[2])]

        self.global_coefficients = global_coefficients

        # Create the specific basis for this pupil
        self.basis = self.create_ptt_basis()

        # Create list of segment coefficients
        self.list_of_coefficients = self.get_list_from_global()

    def create_ptt_basis(self):
        """
        Create the basis needed for getting the per/segment coeffs back

        :return: Poppy Segment_PTT_Basis object for the specified pupil
        """
        pttbasis = poppy.zernike.Segment_PTT_Basis(rings=self._num_rings,
                                                   flattoflat=self.flat_to_flat,
                                                   gap=self.gap,
                                                   segmentlist=self._segment_list)
        return pttbasis

    def create_wavefront_from_global(self, global_coefficients):
        """
        Given an list of global coefficients, create wavefront

        :param global_coefficients: list of global zernike coefficients in the form
                                    [piston, tip, tilt, defocus, ...] (Noll convention)
        :return: Poppy ZernikeWFE object, the global wavefront described by the input coefficients
        """
        wavefront = poppy.ZernikeWFE(radius=self.radius, coefficients=global_coefficients)
        wavefront_out = wavefront.sample(wavelength=self.wavelength,
                                         grid_size=2*self.radius,
                                         npix=512, what='opd')
        return wavefront_out

    def get_coeffs_from_pttbasis(self, wavefront):
        """
        From a the speficic pttbasis, get back the coeff_list that will be sent as
        a command to the Iris AO

        :param wavefront: Poppy ZernikeWFE object, the global wavefront over the
                          pupil
        :return: list, (piston, tip, tilt) values for each segment in the pupil
                 in units of [m] for piston, and [rad] for tip and tilt
        """
        coeff_list = poppy.zernike.opd_expand_segments(wavefront, nterms=self.num_terms,
                                                        basis=self.basis)
        coeff_list = np.reshape(coeff_list, (self.number_segments_in_pupil, 3))
        return coeff_list

    def get_list_from_global(self):
        """
        From a global coeff list, get back the per-segment coefficient list

        :return: list of coefficients for piston, tip, and tilt, for your pupil
        """
        wavefront = self.create_wavefront_from_global(self.global_coefficients)
        coeffs_list = self.get_coeffs_from_pttbasis(wavefront)

        return coeffs_list

    def to_dm_list(self):
        """
        Convert the PTT list to DM hardware units so that it can be passed to the
        SegmentDmCommand class

        :return: list of coefficients for piston, tip, and tilt, for your pupil
        """
        input_list = self.list_of_coefficients
        # Convert from Poppy's m, rad, rad to the DM units
        input_list = convert_ptt_units(input_list, tip_factor=-1, tilt_factor=1,
                                       starting_units=(u.m, u.rad, u.rad),
                                       ending_units=self.dm_command_units)
        coeffs_list = round_ptt_list(input_list)

        return coeffs_list
