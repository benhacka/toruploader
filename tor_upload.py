#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from sitemodules.dlfree import DlFreeModule
from sitemodules.anonfamily import AnonFile, BayFile,\
    LetsUpload, MinFil, MyFile

file_sharing_service_dict = dict(
    dlfree=DlFreeModule(),
    anonfile=AnonFile(),
    bayfile=BayFile(),
    letsupload=LetsUpload(),
    minfil=MinFil(),
    myfile=MyFile()
)


def arg_parser():
    parser = argparse.ArgumentParser()

    module = 'Upload sites: '
    for key, value in file_sharing_service_dict.items():
        module += '({}: {}) '.format(key, value.url)
    parser.add_argument('site', choices=file_sharing_service_dict.keys(),
                        help=module)

    path = 'Folder with files from which you want to upload files'
    parser.add_argument('path', help=path)

    result_filename = """Filename with result 
    (default ~/TUpl/%%upload_folder_name%%_%%root_domain%%.txt) 
    if filename w/o abs path is saved to a ~/TUpl/ 
    where '~' is a user's home directory"""
    parser.add_argument('-r', '--result', help=result_filename,
                        default='')

    filter_extensions = """Extensions (with dot - ".") 
        separated by space of files to be uploaded. 
        You need to enclose the expression in quotation marks if you 
        want space in filter.
        Regular expressions are accepted here. All dot characters are
        interpreted as characters that is with a backslash ("." -> "\.")
        For example: 
        If you want to upload all RARs: .rar 
        If you want to upload only partial RARs: .part\d+.rar
        If you want to upload all jpeg's and png's: .jpeg .png
        W/o dot ('rar') noraro.zip is file to upload. You also can
        filtered name here img\d+ good for img001.png. 
        Single *, + and ? are prohibited and will be deleted.
        To get help and check regular  you can visit: 
        https://pythex.org/
        (default all files in the folder)"""
    parser.add_argument('-f', '--filter', nargs='+', help=filter_extensions,
                        default=None)

    exclude = """Key for NO exclude. 
        Excludes duplicate files from the list for upload check
        %%upload_name%% and %%download_link%%.
        After stopping the script and running one with the same 
        path and result file, it will continue to upload
        and won't start to upload all the files again.
        So if the upload goes to another site then the same names are
        ignored and the files will be uploaded.
        if False: Files are uploaded from the folder again[?!]
        and write in the results.
        (w/o key - exclude)"""
    parser.add_argument('-ne', '--nexclude', action='store_true',
                        help=exclude)

    number_of_letters = """An integer variable max name length 32 chars
        and min - 3 chars that indicates how many letters should be in 
        the upload filename (name when downloading a file).
        If count < 3 - upload_name: original_filename
        else - rnd_ascii_with_param_length.ext0_if_exist.ext
        For save part random name join with two last extension.
        For example: myarch.part1.rar -> %%rand%%.part1.rar
                     myarch.rar -> %%rand%%.rar
                     myarch.some.ext0.ext -> %%rand%%.ext0.ext
        (default 12)"""
    parser.add_argument('-n', '--number', type=int, help=number_of_letters,
                        default=12)

    tor_port = """An integer variable Tor service port 
        (ports vary from 0 to 2**16-1). If the port
        value is out of range, it's interpreted as loading without a Tor
        To upload a file without a Tor, you can specify tor_port
        as -1 (or less) or 2**16 (or greater).
        (default 9050)"""
    parser.add_argument('-p', '--port', type=int, help=tor_port, default=9050)

    limit = """An integer variable 
    maximum number of asynchronous post-requests.
    (default 3)"""
    parser.add_argument('-l', '--limit', type=int, help=limit, default=3)

    time_out = """An integer variable time for upload a file.
        (default 60*60*2 = 7200 -> 2 hours)"""
    parser.add_argument('-t', '--timeout', type=int, help=time_out,
                        default=7200)

    sort = r"""Key for NO sort. Sort uploads in alphabet order.
        Inserts a sorted list at the end of the result file
        for current module. If there are lines in the file that are
        not related to the current module, it will remain and
        will be on top. For example:
        2.rar:cur\n1.rar:other\n1.rar:cur ->
        1.rar:other\n1.rar:cur\n2.rar:cur
        (w/o key sort)"""
    parser.add_argument('-ns', '--nsort', action='store_true',
                        help=sort)

    open_folder = """Key for open.
        Open folder
        with result file in an explorer if it exists
        (with key open)"""
    parser.add_argument('-o', '--open', action='store_true',
                        help=open_folder)

    ingnore_write = """Key for NO write. Write result in file 
    (w/o key - write)"""
    parser.add_argument('-nw', '--nwrite', action='store_true',
                        help=ingnore_write)

    args = parser.parse_args()
    main_dict = dict(
        files_path=args.path,
        result_filename=args.result,
        filter_extensions=args.filter,
        need_to_exclude_uploaded=bool(args.nexclude ^ 1),
        number_of_letters_in_the_randomise_name=args.number,
        tor_port=args.port,
        upload_limit=args.limit,
        post_req_time_out_sec=args.timeout,
        sort_alphabetically=bool(args.nsort ^ 1),
        open_folder_with_result=args.open,
        write_the_results_to_a_file=bool(args.nwrite ^ 1)
    )
    return args.site, main_dict


if __name__ == '__main__':
    uploader_name, kwargs = arg_parser()
    Uploader = file_sharing_service_dict[uploader_name]
    Uploader(**kwargs)
