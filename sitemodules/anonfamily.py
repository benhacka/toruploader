# -*- coding: utf-8 -*-

from .abstractbase.abstract_anon_family import AnonFamily


class AnonFile(AnonFamily):
    @property
    def url(self):
        return 'https://anonfile.com/'


class BayFile(AnonFamily):
    @property
    def url(self):
        return 'https://bayfiles.com/'


class LetsUpload(AnonFamily):
    @property
    def url(self):
        return 'https://letsupload.cc/'


class MinFil(AnonFamily):
    @property
    def url(self):
        return 'https://minfil.com/'


class MyFile(AnonFamily):
    @property
    def url(self):
        return 'https://myfile.is/'
