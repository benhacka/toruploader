# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import asyncio
import aiofiles
from aiohttp_socks import SocksConnector
import aiohttp
import os
import uuid
from math import ceil
import io
import re
from typing import Tuple, Union
from urllib.parse import urlparse
import platform
import subprocess


class UploaderException(Exception):
    """Still an exception raised in Uploader class"""

    def __init__(self, message, ex_det=None):
        self.message = message
        self.exception_details = str(ex_det)

    def __str__(self):
        return str('{}\n{}'.format(self.message, self.exception_details)) \
            if self.exception_details else str('{}'.format(self.message))


class Uploader(ABC):
    """
    Abstract class - framework for easy writing modules.
    overloaded abstract protect method:  _upload_logic.
    overloaded abstract protect property: _file_maxsize.
    protect methods: _verbose_name, _verbose_size,
                    _get_html_and_url, _post_html_and_url.
    overloaded abstract public property: url.
    protect fields: _counter, _session.
    public methods: __call__.


    Class-constructor use instruction:
    1) Overload property url with return "url" which is the domain
    when downloading the file. For example:
    upload url: https://some.host/
    download link: https://file1.some.host/dl
                   or https://some.host/dl?=file1
    correct url for the case: https://some.host/

    2) Overload method _upload_logic is's an algorithm with input
    arguments: upload_name with the full path and the name of the file
    to upload which must be inserted into the upload form.
    The method should return the upload_name and download link.
    See examples in ready-made modules

    3) Overload property file_maxsize with return int a file max size
    for the site. If the information is unknown, you can put the number
    1 TB = 2**40 or _verbose_size(1, 'TB').
    This is necessary in order not to send post-requests that take
    a long time (fat files), but are guaranteed to return with an error.
    """

    def __init__(self):
        self.__headers = {'User-Agent':
                          'Mozilla/5.0 (Windows NT 6.1; rv:24.0) '
                          'Gecko/20100101 Firefox/24.0'}

    def __call__(self, files_path: str, result_filename: str = '',
                 filter_extensions=None,
                 need_to_exclude_uploaded: bool = True,
                 number_of_letters_in_the_randomise_name: int = 12,
                 tor_port: int = 9050, upload_limit: int = 3,
                 post_req_time_out_sec: int = 60 * 60 * 2,
                 sort_alphabetically: bool = True,
                 open_folder_with_result: bool = False,
                 write_the_results_to_a_file: bool = True) -> None:
        """The main method for calling an instance of a class

        :param files_path: dir path with files to be uploaded
        :param result_filename: file with result
        (default ~/TUpl/%upload_folder_name%_%root_domain%.txt)
        a line in the file is %upload_name%:%download_link%\n
        :param filter_extensions: list of extensions (with dot - ".")
        of files to be uploaded
        (default None which means all files in the folder)
        Regular expressions are accepted here. All dot characters are
        interpreted as characters that is with a backslash ("." -> "\.")
        For 'all files' type "*" here (w/o dot).
        For example, if you want to upload all RARs: filter_extensions
        = ['.rar']. If you want to upload only partial RARs:
        filter_extensions = ['.part\d+.rar']
        -> re in script: '\.part\d+\.rar'. To get help and check regular
        you can visit: https://pythex.org/
        :param need_to_exclude_uploaded: a bool flag (default True)
        if True: Excludes duplicate files from the list for upload check
        %upload_name% and %download_link% (looking for entry self.url)
        After stopping the script and running one with the same path
        and result file, it will continue to upload
        and won't start to upload all the files again.
        So if the upload goes to another site then the same names are
        ignored and the files will be uploaded.
        if False: Files are uploaded from the folder again[?!]
        and write in the results.
        :param number_of_letters_in_the_randomise_name: an integer
        variable (default 12) max name length 32 chars and min - 3 chars
        that indicates how many letters should be in the upload_name
        that will be stored on the site.
        If param < 3 - upload_name: original_filename
        else - upload_name: rnd_ascii_with_param_length.ext0_if_exist.ext
        File names may contain some components that are important
        for the program opening the file.
        For save this part random name join with two last extension.
        For example: myarch.part1.rar -> %rand%.part1.rar
                     myarch.rar -> %rand%.rar
                     myarch.some.ext0.ext -> %rand%.ext0.ext
        :param tor_port: an integer variable (default 9050)
        Tor service port (ports vary from 0 to 2**16-1). If the port
        value is out of range, it's interpreted as loading without a Tor
        To upload a file without a Tor, you can specify tor_port
        as -1 (or less) or 2**16 (or greater).
        :param upload_limit: an integer variable (default 3)
        maximum number of asynchronous post-requests.
        :param post_req_time_out_sec: an integer variable
        (default 60*60*2 = 7200 = 2 hours) time that must pass before
        throwing an exception in post_html_and_dict method.
        In case of native low speed and large size of files
        it makes sense to set more than 2 hours.
        :param sort_alphabetically: sort uploads in alphabet order.
        (default True)
        Inserts a sorted list at the end of the result file
        for current module. If there are lines in the file that are
        not related to the current module, it will remain and
        will be on top. For example:
        2.rar:cur\n1.rar:other\n1.rar:cur ->
        1.rar:other\n1.rar:cur\n2.rar:cur
        :param open_folder_with_result: if true open folder
        with result file in an explorer if it exists.
        :param write_the_results_to_a_file: if true write new results
        to the __result_filename
        :return: list of tuple(%upload_name%, %url%)
        if  _upload_logic has a correct return
        """

        self.__loop = asyncio.get_event_loop()
        self.__connector = SocksConnector.from_url(
            'socks5://localhost:{}'.format(tor_port), rdns=True) \
            if 0 <= tor_port <= 2 ** 16 - 1 else None

        if os.path.splitext(urlparse(self.url).netloc)[-1] == '.onion' \
                and not self.__connector:
            raise UploaderException('To load onion hosts you need'
                                    ' to specify TOR port')
        self.__result_filename = self.__generate_result_name(
            result_filename, files_path)
        self.__count_random_chars \
            = number_of_letters_in_the_randomise_name
        self.__files_dict = self.__get_file_and_name_to_upload(
            files_path, filter_extensions, need_to_exclude_uploaded
        )
        self.__up_semaphore = asyncio.BoundedSemaphore(upload_limit,
                                                       loop=self.__loop)
        self.__post_req_time_out_sec = post_req_time_out_sec
        self._counter = 0  # successful post request counter
        self.__need_to_sort = sort_alphabetically
        self.__open_result_folder = open_folder_with_result
        self.__write_result_to_file = write_the_results_to_a_file
        self._session = None  # main asynchronous aiohttp.ClientSession
        #  initialization in the __main_method
        result = self.__loop.run_until_complete(self.__main_method())
        self.__loop.close()
        return result

    @property
    def __get_root_domain(self):
        return os.path.splitext(urlparse(self.url).netloc.
                                replace('www.', ''))[0]

    @property
    def __get_result_file_path(self):
        return os.path.dirname(self.__result_filename)

    def __generate_result_name(self, result_filename, files_path):
        if os.path.isabs(result_filename):
            return result_filename
        default_path = os.path.join(os.path.expanduser('~'), 'TUpl')
        if result_filename:
            return os.path.join(default_path, result_filename)
        dir_with_files = os.path.normpath(files_path).split(os.sep)[-1]
        url = self.__get_root_domain
        filename = '{}_{}.txt'.format(dir_with_files, url)
        return os.path.join(default_path, filename)

    def __files_with_extensions_and_size(self, files_path, filter_extensions):
        all_files_in_folder = []

        for filename in os.listdir(files_path):
            file_with_path = os.path.join(files_path, filename)
            if os.path.isfile(file_with_path):
                if os.path.getsize(file_with_path) < self._file_maxsize:
                    all_files_in_folder.append(filename)
        if not filter_extensions:
            return all_files_in_folder
        filter_extensions = [ext for ext in filter_extensions if ext not in
                             ['*', '+', '?']]
        if not filter_extensions:
            raise UploaderException('Bad extensions')
        try:
            filter_extensions = "|".join(filter_extensions).replace('.', '\.')
            return [file for file in all_files_in_folder if
                    re.search(filter_extensions, file)]
        except Exception as e:
            raise UploaderException("Can't parse extensions", e)

    def __get_excluded(self, full_line=False):
        if not os.path.exists(self.__result_filename):
            return []

        with open(self.__result_filename) as file:
            return [line.strip().split(':')[0] if not full_line
                    else line.strip() for line in file if
                    len(line.strip().split(':')) > 1 and
                    line.strip().split(':', maxsplit=1)[1].count(
                        self.__get_root_domain)]

    def __sort_results(self):
        if not os.path.exists(self.__result_filename):
            return 0
        with open(self.__result_filename) as file:
            all_results = [line.strip() for line in file]
            if not all_results:
                return 0
        uploaded = sorted(self.__get_excluded(full_line=True))
        other_uploads = [line for line in all_results if line not in uploaded]
        all_lines = other_uploads + uploaded
        with open(self.__result_filename, 'w') as file:
            file.write('\n'.join(all_lines))
            file.write('\n')
        return 1

    def __get_file_and_name_to_upload(self, files_path, filter_extensions,
                                      need_to_exclude_uploaded):
        if platform.system() == "Windows":
            files_path = files_path.strip()
        if not os.path.exists(files_path):
            raise UploaderException(
                'Folder does not exist',
                'Check the correctness of the entered path!')
        if need_to_exclude_uploaded:
            excluded = self.__get_excluded()
        else:
            excluded = []
        all_files = self.__files_with_extensions_and_size(
            files_path, filter_extensions)
        if not all_files:
            print('There are no files in the folder with '
                  'suitable sizes or extensions')
            return dict()
        files = [file for file in all_files if file not in excluded]
        if not files:
            print('All files from the folder have already been uploaded to '
                  + self.url)
            return dict()
        return self.__generate_file_pairs_dict(files, files_path)

    @staticmethod
    def __get_ext_of_file(filename, max_parts_count=2):
        ext = re.findall('(\.\w+)(?:|$)', filename)[-max_parts_count:]
        ext = "".join(ext) if ext else ""
        return ext

    def __generate_file_pairs_dict(self, files, file_path):
        def _wp(file):
            return os.path.join(file_path, file)

        def _gen_rand():
            return uuid.uuid4().hex[:self.__count_random_chars]

        files_dict = {}
        if self.__count_random_chars < 3:
            for filename in files:
                files_dict[_wp(filename)] = filename
            return files_dict

        files_ext = [self.__get_ext_of_file(filename) for filename in files]
        files_wo_ext = [filename.replace(ext, '')
                        for filename, ext in zip(files, files_ext)]
        random_names = dict((filename, _gen_rand()) for filename
                            in set(files_wo_ext))
        random_names = [random_names[file_wo_ext] + ext for file_wo_ext, ext
                        in zip(files_wo_ext, files_ext)]
        for filename, random_name in zip(files, random_names):
            files_dict[_wp(filename)] = random_name
        return files_dict

    async def __main_method(self):
        if len(self.__files_dict):
            async with aiohttp.ClientSession(
                    connector=self.__connector, loop=self.__loop,
                    headers=self.__headers) as self._session:

                tasks = [self.__wrapped_upload_logic(file, filename)
                         for file, filename in self.__files_dict.items()]
                result = await asyncio.gather(*tasks)
        else:
            result = []
        failed = len(self.__files_dict) - self._counter
        # in fact, the result message may be incorrect if the uploading
        # logic was incorrectly implemented
        if not failed and len(self.__files_dict):
            print('All files were uploaded successfully.')
        elif failed:
            print('Failed to upload {} files!'.format(failed))
        if self.__need_to_sort and self.__sort_results():
            print('Result file were sorted')
        path = self.__get_result_file_path
        if not os.path.exists(path) or not self.__open_result_folder:
            return result
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["explorer", path])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print("Can't open result folder: {}".format(str(e)))
        finally:
            return result

    async def __wrapped_upload_logic(self, file, filename):
        try:
            arg = await self._upload_logic(file, filename)
            if len(arg) != 2:
                print('Error in _upload_logic module. '
                      'The method should return a tuple of two elements')
                return arg
            filename, url = arg
            if self.__write_result_to_file:
                if not url:
                    return filename, url
                try:
                    await self.__write_result(filename, url)
                except UploaderException as e:
                    print('{} {}'.format(str(e), filename))
                    return filename, url
            else:
                return file, url
        except Exception as e:
            print(e)
            return filename, None

    async def __write_result(self, filename: str, url: str) -> None:
        """
        The method writes arguments (upload_name, url) to a result file.

        :param filename: upload_name w/o absolute file path
        :param url: download link
        :return: None
        """
        result_dir = self.__get_result_file_path
        try:
            if not os.path.exists(result_dir):
                os.makedirs(result_dir, exist_ok=True)
            async with aiofiles.open(self.__result_filename, 'a') as result:
                await result.write('{}:{}\n'.format(filename, url))
                await result.flush()
        except Exception as e:
            raise UploaderException(
                "Error while writing results to the file", e)

    @staticmethod
    def _verbose_name(filename: str) -> str:
        """
        Just a wrapper over a os.path.basename,
        removes path from the upload_name

        :param filename: upload_name with path
        :return: upload_name w/o path
        """
        return os.path.basename(filename)

    @staticmethod
    def _verbose_size(size: float, dimension: str) -> int:
        """
        Get int size form size [dimension].

        :param size: size without dimension
        :param dimension: dimension: B, KB, MB, GB or TB
        :return: int size
        """
        dimension_int = dict(
            b=1,
            kb=2 ** 10,
            mb=2 ** 20,
            gb=2 ** 30,
            tb=2 ** 40).get(dimension.lower())
        try:
            return int(ceil(dimension_int * size))
        except TypeError:
            raise UploaderException('Bad dimension', 'Use: B, KB, MB, GB or '
                                                     'TB (case insensitive)')

    async def _get_html_and_url(self, get_url: str, verify_ssl: bool = True) \
            -> Tuple[str, str]:
        """
        Return result of get-request - tuple(html_response, url)
        Last url needed in case of redirect. If there was no redirection
        it should be equivalent to the get_url from the arguments.

        :param get_url: link for get-request
        :param verify_ssl: relax ssl certification checks
        set to false only in very special cases when it's impossible to
        fundamentally solve the problem like:
        'SSL handshake failed on verifying the certificate'
        :return: (html, url)
        """
        try:
            async with self._session.get(get_url, verify_ssl=verify_ssl) \
                    as res:
                return await res.text(), res.__dict__['_real_url']
        except Exception as e:
            raise UploaderException('Error getting {}'.format(get_url), e)

    async def _post_html_and_url(self, post_url: str,
                                 form_data: aiohttp.FormData, *,
                                 verify_ssl: bool = True) -> \
            Tuple[str, str, Tuple[int, int]]:
        """
        Return result of post-request -
        tuple(html_response, url, tuple(uploaded_counter, total_files)
        Url needed in case of redirect. If there was no redirection,
        then it should be equivalent to the link from the arguments.
        Last tuple is informational and can be useful for console output
        .
        :param post_url: link for post-request
        :param form_data: form-data for post-request Must contain all
        fields that are transmitted during post-request including file.
        Examples of forms in ready-made modules
        :param verify_ssl: look at _get_html_and_url doc-string
        :return: (html, url)
        """

        try:
            file = [_[2] for _ in form_data.__dict__['_fields']
                    if type(_[2]) == io.BufferedReader][0]
        except IndexError:
            raise UploaderException('Form w/o file')

        real_file_name = file.name
        verbose_file_name = self._verbose_name(real_file_name)

        if os.path.getsize(real_file_name) > self._file_maxsize:
            raise UploaderException('File exceed the maximum size',
                                    'File is {}'.format(verbose_file_name))
        try:
            async with self.__up_semaphore:
                print('Uploading: {}'.format(verbose_file_name))
                async with self._session.post(
                        post_url, data=form_data,
                        timeout=self.__post_req_time_out_sec,
                        verify_ssl=verify_ssl) as res:
                    html = await res.text()
                    self._counter += 1
                    counter = (self._counter, len(self.__files_dict))
                    # print(verbose_file_name + ' uploaded')
                    return html, res.__dict__['_real_url'], counter
        except Exception as e:
            raise UploaderException('An error occurred while uploading {}!'.
                                    format(verbose_file_name), e)

    @abstractmethod
    async def _upload_logic(self, file_with_path: str, upload_name: str,
                            **kwargs) -> Tuple[str, Union[str, None]]:
        """An abstract method in which you should describe
        the basic logic of the download from your file hosting, you
        can see an example in ../dlfree.py or ./abstract_anon_family.py.

        :param file_with_path: real filename with path
        :param upload_name: name of the file to be downloaded
        this name must be inserted into the form in the filename field,
        where the file (file_with_path) itself is inserted
        :param kwargs: special arguments for recursively calling
        a method if it necessary.
        :return: (%real_file_name%, %url% or None)
        """

    @property
    @abstractmethod
    def url(self) -> str:
        """url for checking in result file
        it is recommended to enter the correct link so that
        the files do not load several times during restart.
        :return: url or part of url that is in the file download path
        from the site.
        """

    @property
    @abstractmethod
    def _file_maxsize(self) -> int:
        """This can be useful for services with file size restrictions,
        if this property is correctly initialized, then files with
        an invalid size won't be uploaded.

        If the file is larger than the maximum allowed,
        it will throw out an exception, you need to catch
        it in upload_logic

        For example, if the maximum file size for your file
        hosting service is 0.5 GB (=512 MB),
        you can override a property like this:

        @property
        def file_maxsize(self):
            return 2**30//2

        or better like this:

        @property
        def file_maxsize(self):
            return _verbose_size(0.5, 'gb')

        :return: int count of bytes
        """
