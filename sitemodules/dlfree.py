# -*- coding: utf-8 -*-

from .abstractbase.abstract_module import Uploader, UploaderException

import aiohttp
import re
import time


class DlFreeModule(Uploader):

    async def _upload_logic(self, file_with_path, upload_name, n=None):
        verbose_name = self._verbose_name(file_with_path)
        try:
            html, _ = await self._get_html_and_url(self.url + 'index_nojs.pl')
        except UploaderException as e:
            print('{} for {}'.format(str(e), verbose_name))
            return verbose_name, None
        # BeautifulSoup sucks!
        # Regular expressions are our everything!
        up_link = re.findall(r'<form action="/(.*?)" '
                             r'enctype="multipart/form-data"', html)
        if up_link:
            link = self.url + up_link[0]
        else:
            print("Error: can't get post upload url")
            return verbose_name, None

        with open(file_with_path, 'rb') as file:
            form_data = aiohttp.FormData()
            form_data.add_field(name='mail1', value='')
            form_data.add_field(name='mail2', value='')
            form_data.add_field(name='mail3', value='')
            form_data.add_field(name='mail4', value='')
            form_data.add_field(name='message', value='')
            form_data.add_field(name='ufile', value=file,
                                filename=upload_name)
            try:
                _, dl_link, counter = await self._post_html_and_url(
                    link, form_data)
            except UploaderException as e:
                print('{} for {}'.format(str(e), verbose_name))
                return verbose_name, None

        start_time = time.time()
        print('Waiting download link for {}'.format(verbose_name))
        while time.time() - start_time <= 30 * 60:
            try:
                html, _ = await self._get_html_and_url(dl_link)
            except UploaderException as e:
                print('{} for {}'.format(str(e), verbose_name))
                break
            current_dl_link = re.findall(
                'suivante: <a class="underline" href="(.*?)"', html
            )
            if current_dl_link:
                current_dl_link = current_dl_link[0]
                print('Got link for {} as {}: {} [{}/{}]'.format(
                    verbose_name, upload_name, current_dl_link, *counter))
                return verbose_name, current_dl_link
            else:
                time.sleep(5)
        if time.time() - start_time > 30 * 60:
            print('Uploaded but getting time out for {}'.format(verbose_name))
        self._counter -= 1
        return verbose_name, None

    @property
    def url(self):
        return 'http://dl.free.fr/'

    @property
    def _file_maxsize(self):
        return self._verbose_size(1, 'gb')
