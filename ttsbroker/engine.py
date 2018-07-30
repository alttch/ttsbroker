__author__ = "Altertech Group, https://www.altertech.com/"
__copyright__ = "Copyright (C) 2018 Altertech Group"
__license__ = "Apache License 2.0"
__version__ = "0.0.1"

import importlib
import os
import json
import logging

import sounddevice
import soundfile

from hashlib import sha256


class Engine(object):

    def __init__(self, **kwargs):
        """
        Args:
            storage_dir: directory where audio files are permantently stored
            cache_dir: directory where audio files are cached
            cache_format: cache file format, wav(default) or ogg
            device: playback device (list: python3 -m sounddevice)
            gain: default gain
            provider: provider module
            provider_options: default provider options (voice, lang etc.)

        Raises:
            ModuleNotFoundError: tts provider module not found
            Exception: other errors
        """
        self.provider = None
        self.key = None
        self.provider_options = kwargs.get('provider_options', {})
        self.storage_dir = kwargs.get('storage_dir')
        self.cache_dir = kwargs.get('cache_dir')
        self.cache_format = kwargs.get('cache_format', 'wav')
        self.gain = kwargs.get('gain', 0)
        if 'provider' in kwargs: self.set_provider(kwargs['provider'])
        if 'device' in kwargs: self.set_device(kwargs['device'])

    def set_provider(self, provider):
        """Set TTS provider

        Args:
            provider: provider module

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ModuleNotFoundError: tts provider module not found
            Exception: other errors
        """
        try:
            provider_mod = importlib.import_module(
                'ttsbroker.providers.%s' % provider)
        except:
            self._log_error(
                'unable to import TTS provider, module %s' % provider)
            return False
        try:
            self.provider = provider_mod.TTSProvider()
        except:
            self._log_error('unable to init TTS provider, module %s' % provider)
            return False
        self._log_debug('provider set: %s' % provider)
        return True

    def set_device(self, device):
        """Set playback device for sounddevice mod

        Args:
            device: playback device (list: python3 -m sounddevice)

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ModuleNotFoundError: tts provider module not found
            Exception: other errors
        """
        sounddevice.default.device = device
        self._log_debug('playback device set: %s' % device)
        return True

    def set_key(self, key, preload=True):
        """Set provider key (look TTS provider mod documentation)

        Args:
            key: json file or dict
            preload: if True - preload key from the file

        Returns:
            bool: True if successful, False otherwise

        Raises:
            FileNotFoundError: key file not found
            json.decoder.JSONDecodeError: file decode error
            Exception: other errors
        """
        if isinstance(key, str):
            f = ', file: %s' % key
        else:
            f = ''
        self._log_debug('setting key' + f)
        if not isinstance(key, str) and not isinstance(key, dict):
            self._log_error('invalid key format')
            return False
        if preload and isinstance(key, str):
            self._log_debug('preloading key, file: %s' % key)
            self.key = json.load(open(key))
        else:
            self.key = key
        return True

    def say(self, text, **kwargs):
        """Say text or generate audio file

        Args:
            text: text to say
            gain: gain control (-10..inf), float, 0 - default volume
            options: audio generation options
            use_cache: set False to skip looking for a data in the local
                       storage/cache
            store_cache: set False to skip saving a data in the local cache
            cache: set both use_cache and store_cache
            generate_only: set True to skip playback

        Returns:
            bool: True if successful, False otherwise

        Raises:
            Exception: a lot of
        """
        if not self.provider:
            self._log_error('no tts provider set')
            return False
        gain = float(kwargs.get('gain', self.gain))
        use_cache = kwargs.get('use_cache', True)
        store_cache = kwargs.get('store_cache', True)
        cache = kwargs.get('cache')
        options = kwargs.get('provider_options', self.provider_options)
        if cache is not None:
            use_cache = cache
            store_cache = cache
        datablock = {'t': text, 'o': options}
        datahash = sha256(json.dumps(datablock).encode()).hexdigest()
        datafile = '%s/%s.%s' % (datahash[:2], datahash, self.cache_format)
        data = None
        from_cache = False
        self._log_debug('saying text datahash %s' % datahash)
        if use_cache:
            fname = None
            if self.storage_dir and os.path.isfile(
                    '%s/%s' % (self.storage_dir, datafile)):
                fname = '%s/%s' % (self.storage_dir, datafile)
            elif self.cache_dir and os.path.isfile(
                    '%s/%s' % (self.cache_dir, datafile)):
                fname = '%s/%s' % (self.cache_dir, datafile)
            if fname:
                try:
                    self._log_debug('using cached file for %s' % datahash)
                    data, rate = soundfile.read(fname)
                    if data is None or not rate: raise
                    from_cache = True
                except:
                    self._log_error('broken audio file: %s' % fname)
                    return False
        key = json.load(open(self.key)) if \
                isinstance(self.key, str) else self.key
        if data is None:
            self._log_debug('generating audio for %s' % datahash)
            data, rate = self.provider.generate_audio(text, key, **options)
        if data is None or not rate:
            self._log_error('audio generation failed')
            return False
        if not from_cache and self.cache_dir and store_cache and os.path.isdir(
                self.cache_dir):
            self._log_debug('storing audio for %s in cache' % datahash)
            if not os.path.isdir(self.cache_dir + '/' + datahash[:2]):
                os.mkdir(self.cache_dir + '/' + datahash[:2])
            soundfile.write('%s/%s' % (self.cache_dir, datafile), data, rate)
        if not kwargs.get('generate_only'):
            if gain: data = data * self._gain_multiplier(gain)
            sounddevice.play(data, rate, blocking=kwargs.get('wait', True))
        return True

    # internal functions

    def _log_debug(self, msg):
        logging.debug('ttsbroker: %s' % msg)

    def _log_error(self, msg, raise_exception=True):
        logging.error('ttsbroker: %s' % msg)
        if raise_exception: raise Exception(msg)

    def _gain_multiplier(self, gain):
        if not gain:
            g = 1.0
        elif gain > 0:
            g = 1 + gain / 10.0
        elif gain > -10:
            g = 1 - abs(gain) / 10.0
        else:
            g = 0.0
        return g