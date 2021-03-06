"""
Generic data class where all others should be derived from.
"""
import uuid
from abc import ABC, abstractmethod
import numpy as np
from pulse_lib.segments.utility.segments_c_func import get_effective_point_number
from pulse_lib.segments.data_classes.lru_cache import LruCache

import copy

class parent_data(ABC):
    """
        Abstract class hosting some functions that take care of rendering and caching of data and
        makes a template for default functions that are expected in a data object
    """
    start_time = 0
    software_marker_data = dict()

    waveform_cache = LruCache(100)

    def __init__(self):
        self.id = uuid.uuid4()

    @classmethod
    def set_waveform_cache_size(cls, size):
        '''
        Set the new (maximum) size of the waveform cache.
        The cache is cleared when its size changes.
        '''
        if size != cls.waveform_cache.max_size:
            cls.waveform_cache = LruCache(size)

    @classmethod
    def clear_waveform_cache(cls):
        '''
        Clears the waveform cache (freeing memory).
        '''
        # clear the cache by initializing a new one of the same size
        cls.waveform_cache = LruCache(cls.waveform_cache.max_size)

    @abstractmethod
    def append():
        raise NotImplemented

    @abstractmethod
    def slice_time():
        raise NotImplemented

    @abstractmethod
    def reset_time(time = None, extend_only = False):
        raise NotImplemented

    @abstractmethod
    def wait(time):
        raise NotImplemented

    @abstractmethod
    def get_vmax(self,sample_rate):
        '''
        Calculate the maximum voltage in the current segment_single.
        Args:
            sample_rate (double) :  rate at which is samples (in Hz)
        '''
        raise NotImplemented

    @abstractmethod
    def get_vmin(self,sample_rate):
        '''
        Calculate the maximum voltage in the current segment_single.
        Args:
            sample_rate (double) :  rate at which is samples (in Hz)
        '''
        raise NotImplemented

    @abstractmethod
    def integrate_waveform(self, pre_delay, post_delay, sample_rate):
        '''
        takes a full integral of the currently scheduled waveform.
        Args:
            start_time (double) : from which points the rendering needs to start
            stop_time (double) : to which point the rendering needs to go (default (-1), to entire segment)
            sample_rate (double) : rate at which the AWG will be run
        Returns:
            integrate (double) : the integrated value of the waveform (unit is mV/sec).
        '''
        raise NotImplemented

    @abstractmethod
    def __add__():
        raise NotImplemented

    @abstractmethod
    def __mul__():
        raise NotImplemented

    @abstractmethod
    def __copy__():
        raise NotImplemented

    @abstractmethod
    def _render(self, sample_rate, pre_delay = 0, post_delay = 0):
        '''
        make a full rendering of the waveform at a predetermined sample rate. This should be defined in the child of this class.
        '''
        raise NotImplemented

    def add_software_marker(self, marker_name, time):
        '''
        add a marker in software (used as arguments for HVI commands)

        Args:
            marker_name (str) : name of the maker
            time (double) : time in ns where to apply the marker
        '''
        self.software_marker_data[marker_name] = time

    def render(self, pre_delay = 0, post_delay = 0, sample_rate=1e9):
        '''
        renders pulse
        Args:
            pre_delay (double) : amount of time to put before the sequence the rendering needs to start
            post_delay (double) : to which point in time the rendering needs to go
            sample_rate (double) : rate at which the AWG will be run
        returns
            pulse (np.ndarray) : numpy array of the pulse
        '''

        # If no render performed, generate full waveform, we will cut out the right size if needed
        cache_entry = self._get_cached_data_entry()
        if cache_entry.data is None or cache_entry.data['sample_rate'] != sample_rate:

            pre_delay_wvf = pre_delay
            if pre_delay > 0:
                pre_delay_wvf = 0
            post_delay_wvf = post_delay
            if post_delay < 0:
                pre_delay_wvf = 0

            cache_entry.data = {
                'sample_rate' : sample_rate,
                'waveform' : self._render(sample_rate, pre_delay_wvf, post_delay_wvf),
                'pre_delay': pre_delay,
                'post_delay' : post_delay
            }

        # get the waveform
        my_waveform = self.get_resized_waveform(pre_delay, post_delay)

        return my_waveform

    def _get_cached_data_entry(self):
        return self.waveform_cache[self.id]


    def get_resized_waveform(self, pre_delay, post_delay):
        '''
        extend/shrink an existing waveform
        Args:
            pre_delay (double) : ns to add before
            post_delay (double) : ns to add after the waveform
        Returns:
            waveform (np.ndarray[ndim=1, dtype=double])
        '''
        cached_data = self._get_cached_data_entry().data

        sample_rate = cached_data['sample_rate']*1e-9
        sample_time_step = 1/sample_rate

        pre_delay_pt = get_effective_point_number(pre_delay, sample_time_step)
        post_delay_pt = get_effective_point_number(post_delay, sample_time_step)

        wvf_pre_delay_pt = get_effective_point_number(cached_data['pre_delay'], sample_time_step)
        wvf_post_delay_pt = get_effective_point_number(cached_data['post_delay'], sample_time_step)

        # points to add/remove from existing waveform
        n_pt_before = - pre_delay_pt + wvf_pre_delay_pt
        n_pt_after = post_delay_pt - wvf_post_delay_pt

        # if cutting is possible (prefered since no copying is involved)
        cached_waveform = cached_data['waveform']
        if n_pt_before <= 0 and n_pt_after <= 0:
            if n_pt_after == 0:
                return cached_waveform[-n_pt_before:]
            else:
                return cached_waveform[-n_pt_before: n_pt_after]
        else:
            n_pt = len(cached_waveform) + n_pt_after + n_pt_before
            new_waveform =  np.zeros((n_pt, ))

            if n_pt_before > 0:
                new_waveform[0:n_pt_before] = self.baseband_pulse_data[0,1]
                if n_pt_after < 0:
                    new_waveform[n_pt_before:] = cached_waveform[:n_pt_after]
                elif n_pt_after == 0:
                    new_waveform[n_pt_before:] = cached_waveform
                else:
                    new_waveform[n_pt_before:-n_pt_after] = cached_waveform
            else:
                new_waveform[:-n_pt_after] = cached_waveform[-n_pt_before:]

            if n_pt_after > 0:
                new_waveform[-n_pt_after:] =  self.baseband_pulse_data[-1,1]

            return new_waveform

class data_container(np.ndarray):

    def __new__(subtype, input_type=None, shape = (1,)):
        obj = super(data_container, subtype).__new__(subtype, shape, object)

        if input_type is not None:
            obj[0] = input_type

        return obj

    @property
    def total_time(self):
        shape = self.shape

        self = self.flatten()
        times = np.empty(self.shape)

        for i in range(len(times)):
            times[i] = self[i].total_time

        self = self.reshape(shape)
        times = times.reshape(shape)
        return times

    @property
    def start_time(self):
        shape = self.shape

        self = self.flatten()
        times = np.empty(self.shape)

        for i in range(len(times)):
            times[i] = self[i].start_time

        self = self.reshape(shape)
        times = times.reshape(shape)
        return times

    def __copy__(self):
        cpy = data_container(shape = self.shape)

        for i in range(self.size):
            cpy.flat[i] = copy.copy(self.flat[i])

        return cpy
