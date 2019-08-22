[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]


<br />
<p align="center">
  <a href="https://github.com/benhacka/toruploader">
    <img src="https://cdn-12.anonfile.com/w5E6D93fnb/0d76099a-1566506593/simple.png" alt="Logo" width="100" height="100">
  </a>
  <h3 align="center">Tor uploader</h3>

  <p align="center">
    <a href="https://github.com/benhacka/toruploader/issues">Report Bug</a>
    ·
    <a href="https://github.com/benhacka/toruploader/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
  * [Usage script](#usage-script)
  * [Construct own module to upload](#construct-own-module-to-upload)
* [License](#license)
* [Thanks](#thanks)


<!-- ABOUT THE PROJECT -->
## About The Project

Sometimes there is a need to upload a lot of separate files to some file sharing hosting, but this is a tedious task. Recently, I had an idea to automate this process, but to make it different from the usual asynchronous loader - constructor, I decided that the uploader will be through a proxy through a tor. 

Well, it’s like there is something at the out, and it’s kind of even working. :smile:

It seems to me that the main feature is not the loader itself, but the ability to write your module for a site in just a few minutes and easy integrate it into the loader.


### Built With
* [Python 3.7](https://www.python.org/)
* [aiohttp](https://aiohttp.readthedocs.io/)


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

You need a **python version of at least 3.5** for the script working!

### Installation

1. Open the folder in the terminal/console where you want to save the project.
2. Clone the repo
```sh
git clone https://github.com/benhacka/toruploader.git
```
3. Go to the downloaded folder. 
```sh
cd toruploader
```
4. Install requirements`
```sh
pip3 install -r requirements.txt
```



<!-- USAGE EXAMPLES -->
## Usage

### Usage script

Available upload sites:
- http://dl.free.fr/
- Anonfiles file sharing hosts:
  - https://anonfile.com/
  - https://bayfiles.com/
  - https://letsupload.cc/
  - https://minfil.com/
  - https://myfile.is/

For upload files from the folder you need to write something like this in the console:
```sh
python3 tor_upload.py <upl_module> <path_to_folder> [keys]
```

Required arguments are:
- module name
- abs path to folder

There are also some optional arguments that may be useful.

Examples:
Let's imagine a %folder% is some existing folder on the disk with abs path in name.

1. Need to upload all files from %folder% to anonfile.com and open the folder with the created result file with default name. Randomize names by default. Sort the results alphabetically.
```sh
python3 tor_upload.py anonfile "%folder%" -o
```

2. Need to upload all rar files from %folder% to free.fr. Randomize names - 8 chars. Don't sort the results.
```sh
python3 tor_upload.py dlfree "%folder%" -f .rar -n 8 -ns
```

3. Need to upload all jpeg files whose names i have a template like 'img001.jpeg', 'img002.jpeg' from %folder% to bayfiles.com in 10 async threads w/o tor. Save original names. Sort the results alphabetically.
```sh
python3 tor_upload.py bayfiles "%folder%" -l 10 -f 'img\d{3}.jpeg' -p -1 -n 0
# note that in regular expressions you do not need to put 
# a backslash before the dot character!
```

4. Need to upload all files from %folder% to minfil.com and save result to F:/result/myresult.txt (in previous examples, saving was to a file  ~/TUpl/%upload_folder_name%_%root_domain%.txt) and force upload, even if there are already same file names as in the %folder% and same module in myresult.txt. Randomize names by default. Don't sort the results.

```sh
python3 tor_upload.py minfil "%folder%" -r "F:/result/myresult.txt" -ne -ns
```


To get help:
```sh
python3 tor_upload.py -h
```

### Construct own module to upload
Only a few modules are currently available for upload, but it is assumed that you will use the script as a constructor to build your modules.
It's really easy! Let's try.

There are no image file sharing sites in ready-made ones, let's fix this. Choose something... like this - https://www.bilder-upload.eu for example. 

At first, we will inherit the class from the parent template and override all abstract methods

```python
from .abstractbase.abstract_anon_family import Uploader, UploaderException
import aiohttp
import re

class BilderUpload(Uploader):

    async def _upload_logic(self, file_with_path, upload_name, **kwargs):
        pass


    @property
    def url(self):
        return "https://www.bilder-upload.eu"


    @property
    def _file_maxsize(self):
        pass
```

Let's take a look at the start page - "Maximalgröße: 10 MB". Great, now we can override _file_maxsize fully

```python
    @property
    def _file_maxsize(self):
        return self._verbose_size(10, 'mb')
```

Now we need to sniff the traffic to understand upload logic. You can use the standard traffic analyzer for browsers, special software (for example - Charles) or browser plug-ins. I chose this plugin, it is simple and beautiful [Web Sniffer](http://5ms.ru/sniffer/) for test in regular Chrome.

![post req](https://cdn-16.anonfile.com/PfEeDc33nf/adfbd4ac-1566506688/post_req.jpg)

The screenshot shows that the post-request sent to https://www.bilder-upload.eu and answer is also there (without a redirect, this isn't shown on the screenshot). We also see form data on the screenshot. We need to pull out a direct download link on the page that the browser returned to us. I'll use regular expressions for this (I hate BeautifulSoap although I understand its advantages).  
![get result](https://cdn-08.anonfile.com/gbF7D939nc/4795c35e-1566506735/form.jpg)

We will take into account one feature of this picexch, in order to get a direct link without unnecessary clicks, we need to replace 'thumb' with 'upload' in the preview link. And now we can override _upload_logic!

```python
    async def _upload_logic(self, file_with_path, upload_name, **kwargs):
        verbose_name = self._verbose_name(file_with_path)
        regular = '&lt;img src="(.*)" border="1" alt="Bilder-Upload.eu'
        with open(file_with_path, 'rb') as file:
            form_data = aiohttp.FormData()
            form_data.add_field(name='datei', value=file,
                                filename=upload_name)
            form_data.add_field(name='upload', value='Hochladen starten...')

            try:
                html, _, counter = await self._post_html_and_url(
                    self.url, form_data)
            except UploaderException as e:
                print(e)
                return verbose_name, None

            link = re.findall(regular, html)
            if not link:
                self._counter -= 1
                print('Link not found for {}'.format(verbose_name))
                return verbose_name, None
            link = link[0].replace('thumb', 'upload')
            print('uploaded {}: {} [{}/{}]'.format(
                verbose_name, link, *counter))
            return verbose_name, link
```

and now we can add our new module to tor_upload.py
```python
from sitemodules.bilderupload import BilderUpload
```

and add in the file_sharing_service_dict 
```python
file_sharing_service_dict = dict(
	...
    bilderupload=BilderUpload()
)
```

And yeap, that's all ~~folks~~. We wrote a new module and it took about 50 lines.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Thanks

Thanks a lot to [othneildrew](https://github.com/othneildrew) for [Best-README-Template](https://github.com/othneildrew/Best-README-Template)


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/benhacka/toruploader.svg?style=flat-square
[contributors-url]: https://github.com/benhacka/toruploader/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/benhacka/toruploader.svg?style=flat-square
[forks-url]: https://github.com/benhacka/toruploader/network/members
[stars-shield]: https://img.shields.io/github/stars/benhacka/toruploader.svg?style=flat-square
[stars-url]: https://github.com/benhacka/toruploader/stargazers
[issues-shield]: https://img.shields.io/github/issues/benhacka/toruploader.svg?style=flat-square
[issues-url]: https://github.com/benhacka/toruploader/issues
[license-shield]: https://img.shields.io/github/license/benhacka/toruploader.svg?style=flat-square
[license-url]: https://github.com/benhacka/toruploader/blob/master/LICENSE.txt
