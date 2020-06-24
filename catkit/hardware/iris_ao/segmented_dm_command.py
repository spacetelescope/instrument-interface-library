"""
Holds the class SegmentedDmCommand that is used to create a dict that will be sent to the
segmented DM hardware as a command.
"""
from configparser import NoOptionError
import json
import os

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import poppy

from catkit.config import CONFIG_INI
from catkit.hardware.iris_ao import util as segmented_dm_util


class SegmentedDmCommand():
    """
    Handle segmented DM specific commands in terms of piston, tip and tilt (PTT) for
    each segment. Creates a dictionary of the form {seg: (piston, tip, tilt)} that can
    be loaded onto the hardware.

    Units of the loaded command are expected to be in um (for piston) and mrad (for tip and tilt)

    This class does NOT interact with hardware directly.

    :param apply_flat_map: If true, add flat map correction to the data before creating command
    :param dm_config_id: str, name of the section in the config_ini file where information
                         regarding the segmented DM can be found. Default: 'iris_ao'
    :attribute data: dict, Input data, shifted if custom pupil exists in config file
    :attribute apply_flat_map: bool, whether or not to apply the flat map
    :attribute source_pupil_numbering: list, numbering native to data
    :attribute command: dict, Final command with flat if apply_flat_map = True
    :attribute filename_flat: str, path to flat
    :attribute total_number_segments: int, total number of segments in DM
    :attribute active_segment_list: int, number of active segments in the DM

    Optional if not using full DM:
    :attribute number_segments_in_pupil: int, the number of segments in the pupil.

    """
    def __init__(self, apply_flat_map=False, dm_config_id='iris_ao'):
        # Grab things from CONFIG_INI
        self.filename_flat = CONFIG_INI.get(dm_config_id, 'flat_file_ini')
        # Check that the file exists (specifically, are you on the testbed or not)
        if not os.path.exists(self.filename_flat):
            raise ValueError(f"{self.filename_flat} either does not exists or is not currently accessible")

        try:
            self.segments_in_pupil = json.loads(CONFIG_INI.get(dm_config_id, 'active_segment_list'))
            self.number_segments_in_pupil = CONFIG_INI.getint(dm_config_id,
                                                              'active_number_of_segments')
            if len(self.segments_in_pupil) != self.number_segments_in_pupil:
                raise ValueError("The array length active_segment_list does not match the active_number_of_segments in the config.ini. Please update your config.ini.")
        except NoOptionError:
            self.segments_in_pupil = segmented_dm_util.iris_pupil_naming(dm_config_id)

        self.apply_flat_map = apply_flat_map
        self.data = segmented_dm_util.create_zero_array(self.number_segments_in_pupil) #TODO: change this to Nans?
        self.command = None


    def read_new_command(self, segment_values):
        """
        Read a new command and assign to the attribute 'data'

        :param segment_values: str, list. Can be .PTT111, .ini files or a list with piston, tip,
                               tilt values in a tuple for each segment. See the load_command doc
                               string for more information.
        """
        self.data = self.read_command(segment_values)


    def read_command(self, segment_values):
        """
        Read a command from one of the allowed formats

        :param segment_values: str, list. Can be .PTT111, .ini files or a list with piston, tip,
                               tilt values in a tuple for each segment.See the load_command doc
                               string for more information.
        """
        ptt_arr, segment_names = segmented_dm_util.read_segment_values(segment_values)
        if segment_names is not None:
            command_array = []
            for seg_name in self.segments_in_pupil:  # Pull out only segments in the pupil
                ind = np.where(np.asarray(segment_names) == seg_name)[0][0]
                command_array.append(ptt_arr[ind])
        else:
            command_array = ptt_arr
        return command_array


    def get_data(self):
        """ Grab the current shape to be applied to the DM (does NOT include the flat map)
        """
        return self.data


    def to_command(self):
        """ Output command suitable for sending to the hardware driver. The flat
        map will be added only at this stage
        """
        if self.apply_flat_map:
            self.add_map(self.filename_flat)
        command_dict = dict(zip(self.segments_in_pupil, self.data))

        return command_dict


    def update_one_segment(self, segment_ind, ptt_tuple):
        """ Update the value of one segment. This will be ADDED to the current value

        :param segment_ind: int, the index of the segment in the pupil to be updated
                            (see README for relationship between index and segment)
        :param ptt_tuple: tuple with three values for piston, tip, and tilt

        """
        command_array = segmented_dm_util.create_zero_array(self.number_segments_in_pupil)
        command_array[segment_ind] = ptt_tuple

        self.add_map(command_array)


    def add_map(self, segment_values_to_add):
        """
        Add a command to the one already loaded.

        :param new_command: str or array (.PTT111 or .ini file, or array from POPPY)
        """
        original_data = self.get_data()
        new_data = self.read_command(segment_values_to_add)

        #TODO check for nans and handle them
        self.data = [tuple(map(sum, zip(orig, new))) for orig,
                     new in zip(original_data, new_data)]


def load_command(segment_values, apply_flat_map=True, dm_config_id='iris_ao'):
    """
    Loads the segment_values from a file, array, or dictionary and returns a
    SegmentedDmCommand object.

    There are only two allowed segment mappings for the input formats, Native and Centered Pupil.
    See the README for the Iris AO for more details.

    :param segment_values: str, list. Can be .PTT111, .ini files or a list with piston, tip,
                           tilt values in a tuple for each segment. For the list, the first
                           element is the center or top of the innermost ring of the pupil,
                           and subsequent elements continue up and/or clockwise around the
                           pupil (see README for more information)
    :param apply_flat_map: Apply a flat map in addition to the data.

    :return: SegmentedDmCommand object representing the command dictionary.
    """
    dm_command_obj = SegmentedDmCommand(apply_flat_map=apply_flat_map, dm_config_id=dm_config_id)
    dm_command_obj.read_new_command(segment_values)

    return dm_command_obj


## POPPY
def round_ptt_list(ptt_list, decimals=3):
    """
    Make sure that the PTT coefficients are rounded to a reasonable number of decimals

    :param ptt_arr: list, of tuples existing of piston, tip, tilt, values for each
                    segment in a pupil
    """
    return [(np.round(ptt[0], decimals), np.round(ptt[1], decimals),
             np.round(ptt[2], decimals)) for ptt in ptt_list]


def convert_ptt_list(ptt_list, tip_factor, tilt_factor, starting_units, ending_units):
    """
    Convert the PTT list to or from Poppy and the segmented DM.

    Note that this has been created for the IrisAO segmented DMs, therefore
    the tip and tilt values are swapped with what Poppy desginates.

    Poppy to segmented DM:
    - tip_factor = -1
    - tilt_facotr = 1
    - starting_units = (u.m, u.rad, u.rad)
    - ending_units = dm_ptt_units from the config.ini file

    Segmented DM to Poppy
    - tip_factor = 1
    - tilt_facotr = -1
    - starting_units = dm_ptt_units from the config.ini file
    - ending_units = (u.m, u.rad, u.rad)

    """
    converted = [(ptt[0]*(starting_units[0]).to(ending_units[0]),
                  tip_factor*ptt[2]*(starting_units[2]).to(ending_units[2]),
                  tilt_factor*ptt[1]*(starting_units[1]).to(ending_units[1])) for ptt in ptt_list]
    return converted


def get_wavefront_from_coeffs(basis, coeff_array):
    """
    Get the wavefront from the coefficients created by the basis given. This gives
    the per-segment wavefront based on the global coefficients given and the basis
    created.

    :params basis: POPPY Segment_PTT_Basis object, basis created that represents pupil
    :params coeff_array: array, per-segment array of piston, tip, tilt values for
                         the pupil described by basis

    :return wavefront, POPPY wavefront
    """
    wavefront = poppy.zernike.opd_from_zernikes(coeff_array, basis=basis)
    return wavefront


class SegmentedAperture():
    """
    Create a segmented aperture with Poppy using the parameters for the testbed
    and segmented DM from the config.ini file.

    To create an aperture, with the config.ini file loaded, run:
        segmented_aperture_obj = SegmentedAperture()
        my_aperture = segmented_aperture_obj.create_aperture()

    :param dm_config_id: str, name of the section in the config_ini file where information
                         regarding the segmented DM can be found. Default: 'iris_ao'
    :param laser_config_id: str, name of the section in the config_ini file where information
                         regarding the laser can be found. Default: 'thorlabs_source_mcls1'

    :attribute wavelength: int, wavelength of the laser being used
    :attribute outer_ring_corners: bool, whether or not the segmented aperture includes
                                   the corner segments on the outer-most ring. If True,
                                   corner segments are included. If False, they are not
    :attribute center_segment: bool, whether of not the segmented aperture includes the
                               center segment. If True, the center segment is included.
                               If False, it is not.
    :attribute flat_to_flat: float, physical distance from flat to flat side of DM segment
    :attribute gap: int, physical distance between DM segments
    :attribute num_segs_in_pupil: int, number of segments included in the aperture
    """
    def __init__(self, dm_config_id='iris_ao',
                 laser_config_id='thorlabs_source_mcls1'):
        # Parameters specific to testbed setup being used
        self.wavelength = CONFIG_INI.getint(laser_config_id, 'lambda_nm')*u.nm

        # Parameters specifc to the aperture and segmented DM being used
        self.outer_ring_corners = CONFIG_INI.getboolean(dm_config_id, 'include_outer_ring_corners')
        self.center_segment = CONFIG_INI.getboolean(dm_config_id, 'include_center_segment')
        self.flat_to_flat = CONFIG_INI.getfloat(dm_config_id, 'flat_to_flat_mm') * u.mm
        self.gap = CONFIG_INI.getfloat(dm_config_id, 'gap_um') * u.micron
        self.num_segs_in_pupil = CONFIG_INI.getint(dm_config_id, 'active_number_of_segments')

        # Get the specific segments
        self._num_rings = self.get_number_of_rings()
        self._segment_list = self.get_segment_list()


    def create_aperture(self):
        """
        Based on values in config file, create the aperture to be simulated

        :returns: A Poppy HexSegmentedDeformableMirror object for this aperture
        """
        aperture = poppy.dms.HexSegmentedDeformableMirror(name='Segmented DM',
                                                          rings=self._num_rings,
                                                          flattoflat=self.flat_to_flat,
                                                          gap=self.gap,
                                                          segmentlist=self._segment_list)
        return aperture


    def get_segment_list(self):
        """
        Grab the list of segments to be used in your pupil taking into account if your
        aperture has a center segment and/or the segments in the corners of the outer ring.
        This list is passed to Poppy to help create the aperture.

        :param num_rings: int, The number of rings in your pupil
        :return: list, the list of segments
        """
        num_segs = self.number_segments_in_aperture(self._num_rings)
        seglist = np.arange(num_segs)

        if not self.outer_ring_corners:
            inner_segs = seglist[:(num_segs-6*self._num_rings)]
            outer_segs = seglist[(num_segs-6*self._num_rings):]
            outer_segs = np.delete(outer_segs, np.arange(0, outer_segs.size,
                                                         self._num_rings)) # delete corner segs
            seglist = np.concatenate((inner_segs, outer_segs))

        if not self.center_segment:
            seglist = seglist[1:]
        return seglist


    def get_number_of_rings(self, max_rings=7):
        """
        Get the number of rings based on the number of active segments specified in the
        config.ini file. This function can be used for a pupil of up to 7 rings (the max
        allowed in the PTT489 IrisAO model).
        Note that for the PTT489 model the 7th ring does not include the corner segments
        which you will need to make clear.

        :returns: num_rings: int, the number of full rings of hexagonal segments in the aperture
        """
        segs_per_ring = SegmentedAperture.number_segments_in_aperture(max_rings, return_list=True)

        # If no outer corners, you will have 6 fewer segments in that outer ring
        if not self.outer_ring_corners:
            segs_per_ring = [num-6 if num > 6 else num for num in segs_per_ring]
        # If no center segment, you will have 1 fewer segment overall
        if not self.center_segment:
            segs_per_ring = [num-1 for num in segs_per_ring]

        try:
            num_rings = segs_per_ring.index(self.num_segs_in_pupil)
        except ValueError:
            raise ValueError("Invalid number of segments. Please check your config.ini file.")

        return num_rings


    @staticmethod
    def number_segments_in_aperture(number_of_rings=7, return_list=False):
        """
        For a segmented aperture of rings = number_of_rings, give the total number of
        segments in the aperture given an aperture of 1, 2, 3, etc. rings. Will return
        a list of the total number of segments in the *aperture* per ring where the ring
        is indicated by the index in the list.

        param: number_of_rings, int, the number of rings in the aperture

        returns: a list of segments where the index of the value corresponds to the
                 number of rings. For example: index 0 corresponds with the center
                 where there is one segment.
        """
        segs_per_ring = [1,] # number of segments per ring
        for i in np.arange(number_of_rings)+1:
            segs_per_ring.append(segs_per_ring[i-1]+i*6)

        if return_list:
            return segs_per_ring
        else:
            return segs_per_ring[number_of_rings]


class PoppySegmentedCommand(SegmentedAperture):
    """
    Create a segement values array (and dictionary) (in POPPY: wavefront error) using
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

    :attribute radius: float, half of the flat-to-flat distance of each segment
    :attribute num_terms: int, number of zernike terms to be included (3 x number of segments)
    :attribute dm_command_units: list, the units the piston, tip, tilt (respecitvely)
                                 values when coming from the DM or DM command
    :attribute global_coefficents: list of global zernike coefficients in the form
                                [piston, tip, tilt, defocus, ...] (Noll convention)
    :attribute basis: poppy.zernike.Segment_PTT_Basis object, basis based on the characteristics
                      of the segmented DM being used
    :attribute list of coefficients: list of piston, tip, tilt coefficients in units of u, rad, rad
    """
    def __init__(self, global_coefficients,
                 dm_config_id='iris_ao', laser_config_id='thorlabs_source_mcls1'):
        # Initilize parent class
        SegmentedAperture.__init__(self, dm_config_id=dm_config_id, laser_config_id=laser_config_id)

        self.radius = (self.flat_to_flat/2).to(u.m)
        self.num_terms = (self.num_segs_in_pupil) * 3

        # Grab the units of the DM for the piston, tip, tilt values to convert to
        dm_command_units = CONFIG_INI.get(dm_config_id, 'dm_ptt_units').split(',')
        self.dm_command_units = [u.Unit(dm_command_units[0]), u.Unit(dm_command_units[1]),
                                 u.Unit(dm_command_units[2])]

        self.global_coefficients = global_coefficients

        # Create the specific basis for this pupil
        self.basis = self.create_ptt_basis()

        # Create array of coefficients
        self.list_of_coefficients = self.get_array_from_global()


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
        Given an array of global coefficients, create wavefront

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
        From a the speficic pttbasis, get back the coeff_array that will be sent as
        a command to the Iris AO

        :param wavefront: Poppy ZernikeWFE object, the global wavefront over the
                          pupil

        :return: np.ndarray, (piston, tip, tilt) values for each segment in the pupil
                 in units of [m] for piston, and [rad] for tip and tilt
        """
        coeff_array = poppy.zernike.opd_expand_segments(wavefront, nterms=self.num_terms,
                                                        basis=self.basis)
        coeff_array = np.reshape(coeff_array, (self.num_segs_in_pupil, 3))
        return coeff_array


    def get_array_from_global(self):
        """
        From a global coeff array, get back the per-segment coefficient array

        :return: np.ndarray of coefficients for piston, tip, and tilt, for your pupil
        """
        wavefront = self.create_wavefront_from_global(self.global_coefficients)
        coeffs_array = self.get_coeffs_from_pttbasis(wavefront)

        return coeffs_array


    def to_dm_list(self):
        """
        Convert the array into an array that can be passed to the SegmentDmCommand
        """
        input_array = self.list_of_coefficients
        # Convert from Poppy's m, rad, rad to the DM units
        input_array = convert_ptt_list(input_array, tip_factor=-1, tilt_factor=1,
                                       starting_units=(u.m, u.rad, u.rad),
                                       ending_units=self.dm_command_units)
        coeffs_array =  round_ptt_list(input_array)

        return coeffs_array


class DisplayCommand(SegmentedAperture):
    """
    For a Segmented DM command (specifically the PTT list per segment), display
    the wavefront or mirror state.

    This class inherits the SegmentedAperture class.

    :param ptt_list: list, SegmentedDmCommand.data or a list of PTT values
    :param out_dir: str, where to save figures
    :param dm_config_id: str, name of the section in the config_id where information
                         regarding the segmented DM can be found. Default: 'iris_ao'
    :param laser_config_id: str, name of the section in the config_id where information
                         regarding the laser can be found. Default: 'thorlabs_source_mcls1'

    :attribute ptt_list: list, list of piston, tip, tilt values for each segment in aperture.
                    This list has units of (um, mrad, mrad)
    :attribute out_dir: str, where to save figures
    :attribute dm_command_units: list, the units the piston, tip, tilt (respecitvely)
                                 values when coming from the DM or DM command
    :attribute instrument_fov: int, The field of view of the camera being used
    :attribute aperture: poppy.dms.HexSegmentedDeformableMirror object

    """
    def __init__(self, ptt_list, out_dir='', dm_config_id='iris_ao',
                 laser_config_id='thorlabs_source_mcls1', testbed_config_id='testbed'):
        # Initilize parent class
        SegmentedAperture.__init__(self, dm_config_id=dm_config_id, laser_config_id=laser_config_id)
        if ptt_list is None:
            raise ValueError('Your list of Piston, Tip, Tilt values cannot be None')

        # Check for and replace Nans
        self.ptt_list = ptt_list
        self.out_dir = out_dir

        # Grab the units of the DM for the piston, tip, tilt values to convert to
        dm_command_units = CONFIG_INI.get(dm_config_id, 'dm_ptt_units').split(',')
        self.dm_command_units = [u.Unit(dm_command_units[0]), u.Unit(dm_command_units[1]),
                                 u.Unit(dm_command_units[2])]

        # Grab the FOV of the instrument from the config file
        self.instrument_fov = CONFIG_INI.getint(testbed_config_id, 'fov')

        # Create the aperture and apply the shape
        self.aperture = self.create_aperture()
        self.deploy_global_wf()


    def deploy_global_wf(self):
        """
        Put a global wavefront on the Iris AO, from an Iris AO dict input wavefront map.
        """
        # Convert the PTT list from DM to Poppy
        converted_list = convert_ptt_list(self.ptt_list, tip_factor=1, tilt_factor=-1,
                                          starting_units=self.dm_command_units,
                                          ending_units=(u.m, u.rad, u.rad))

        for seg, values in zip(self.aperture.segmentlist, converted_list):
            # conversion from um and mrad to m and rad
            self.aperture.set_actuator(seg, values[0], values[1], values[2])


    def display(self, display_wavefront=True, display_psf=True, root=''):
        """
        Display either the deployed mirror state ("wavefront") or the PSF created
        by this mirror state.

        :params display_wavefront: bool, If true, display the deployed mirror state
        :params display_psf: bool, If true, display the simulated PSF created by the
                             mirror state
        """
        if root:
            root = f'{root}_'
        if display_wavefront:
            self.plot_wavefront(root)
        if display_psf:
            self.plot_psf(root)


    def plot_wavefront(self, root):
        """
        Plot the deployed mirror state ("wavefront")
        """
        plt.figure()
        self.aperture.display(what='opd', title='Shape put on the active segments')
        plt.savefig(os.path.join(self.out_dir, f'{root}shape_on_dm.png'))
        plt.close()


    def plot_psf(self, root):
        """
        Plot the simulated PSF based on the mirror state
        """
        pixelscale = self.instrument_fov/512. # arcsec/px, 512 is size of image
        plt.figure()
        osys = poppy.OpticalSystem()
        osys.add_pupil(self.aperture)
        osys.add_detector(pixelscale=pixelscale, fov_arcsec=self.instrument_fov)

        psf = osys.calc_psf(wavelength=self.wavelength)
        poppy.display_psf(psf, vmin=10e-8, vmax=10e-2,
                          title='PSF created by the shape put on the active segments')
        plt.savefig(os.path.join(self.out_dir, f'{root}simulated_psf.png'))
        plt.close()
