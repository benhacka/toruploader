# -*- coding: utf-8 -*-

from .abstract_module import Uploader, UploaderException
from abc import ABC, abstractmethod
import aiohttp
import re


class AnonFamily(Uploader, ABC):

    @abstractmethod
    def url(self):
        pass

    @property
    def _file_maxsize(self):
        return self._verbose_size(20, 'gb')

    async def _upload_logic(self, file_with_path, upload_name, n=None):
        return await self.anon_family_upload_logic(
            self.url, file_with_path, upload_name)

    async def anon_family_upload_logic(self, url, file_with_path,
                                       filename):
        verbose_name = self._verbose_name(file_with_path)
        try:
            html, _ = await self._get_html_and_url(url)
        except UploaderException as e:
            print('{} for {}'.format(str(e), verbose_name))
            return verbose_name, None

        token = re.findall(r'name="_token" value="(.*?)"', html)
        if not token:
            print('Error before posting {}'.format(verbose_name))
            return verbose_name, None

        token = token[0]
        with open(file_with_path, 'rb') as file:
            form_data = aiohttp.FormData()
            form_data.add_field(name='file', value=file, filename=filename)
            form_data.add_field(name='_token', value=token)
            try:
                html, _, counter = await self._post_html_and_url(
                    url, form_data)
            except UploaderException as e:
                print('{} for {}'.format(str(e), verbose_name))
                return verbose_name, None

            dl_link = re.findall(r'file-input" type="text" value="(.*?)"',
                                 html)
            if not dl_link:
                print("Error: can't found download link on the page for "
                      "{}".format(verbose_name))
                self._counter -= 1
                return verbose_name, None
            dl_link = dl_link[0]
            print('{} uploaded as {}: {} [{}/{}]'.format(
                verbose_name, filename, dl_link, *counter))
            try:
                await self._write_result(verbose_name, dl_link)
            except UploaderException as e:
                print(e)
            return verbose_name, dl_link
