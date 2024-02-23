#!/usr/bin/python3

"""calibre2jellyfin.py

   Python script to construct a Jellyfin ebook library from a Calibre library.

   2023-11-17 initial revision
   author Shawn C. Powell
"""

import sys
import configparser
import argparse
import re
import logging
from pathlib import Path
from xml.dom import minidom
from os import stat
from shutil import copyfile

# ------------------
#   Globals
# ------------------


CONFIG_FILE_PATH = Path(Path(__file__).stem + '.cfg')
CMDARGS = None


# ------------------
#   Functions
# ------------------

def find_book(book_file_types, book_folder_src_path):

    """Locates first instance of a file having an configured book extension

        book_file_types         [], list of file extensions identifying books (exclude periods)
        book_folder_src_path    pathlib.Path, full path to book folder to search

        returns                 pathlib.Path, full path to located book file
                                None if not found
    """

    for type_ext in book_file_types:
        for book_file_path in book_folder_src_path.glob('*.' + type_ext):
            return book_file_path
    return None


def find_metadata(book_folder_src_path):

    """Locates first instance of a metadata file (one w an .opf extension)

        book_folder_src_path    pathlib.Path, full path to book folder to search

        returns                 pathlib.Path, full path to metadata file
                                None if not found
    """

    for metadata_file_path in book_folder_src_path.glob('*.opf'):
        return metadata_file_path
    return None


def find_cover(book_folder_src_path):

    """Locates instance of a book cover image

        book_folder_src_path    pathlib.Path, full path to book folder to search

        returns                 pathlib.Path, full path to cover image
                                None if not found
    """

    for cover_file_path in book_folder_src_path.glob('cover.jpg'):
        return cover_file_path
    return None


def read_metadata_file_fallback(metadata_file_path):

    """Reads book metadata, use in case of UnicodeDecodeError

        metadata_file_path    pathlib.Path, full path to metadata file

        returns             minidom doc object
                            None on failure

        This is a workaround for some unicode decode errors that
        were encountered during testing under Windows (10).
        It's puzzling because using the same Calibre library
        under Linux did not suffer from the issue.

    """

    # open the metadata file and create a document object
    try:
        with open(metadata_file_path, 'r', encoding='ascii', errors='backslashreplace') as docfile:
            doc = minidom.parse(docfile)
    except OSError as excep:
        logging.warning('Could not read metadata file "%s": %s', metadata_file_path, excep)
        return None
    except Exception as excep:
        logging.warning('Could not parse metadata file "%s": %s', metadata_file_path, excep)
        return None

    return doc


def read_metadata_file(metadata_file_path):

    """Reads book metadata

        metadata_file_path    pathlib.Path, full path to metadata file

        returns             minidom doc object
                            None on failure
    """

    # open the metadata file and create a document object
    try:
        with open(metadata_file_path, 'r', encoding='utf8') as docfile:
            doc = minidom.parse(docfile)
    except OSError as excep:
        logging.warning('Could not read metadata file "%s": %s', metadata_file_path, excep)
        return None
    except UnicodeDecodeError:
        return read_metadata_file_fallback(metadata_file_path)
    except Exception as excep:
        logging.warning('Could not parse metadata file "%s": %s', metadata_file_path, excep)
        return None

    return doc


def get_metadata(metadata_file_path):
    """Creates a miniDOM object from the metadata file and extracts
        various strings and elements of interest.

        metadata_file_path    pathlib.Path, full path to metadata file

        Returns ()          doc, minidom xml doc object
                            str, name of series, empty str if none
                            str, book index in series, empty str if none
                            element, <dc:title>
                            element, <meta name="calibre:title_sort" content="001 - Book Title"/>
                            element, <dc:description>
    """

    series = ''
    series_index = ''
    doc = None
    titleel = None
    sortel = None
    descel = None

    if not metadata_file_path:
        return doc, series, series_index, titleel, sortel, descel

    doc = read_metadata_file(metadata_file_path)
    if not doc:
        return doc, series, series_index, titleel, sortel, descel

    # get series info and other elements

    titleel = doc.getElementsByTagName('dc:title')[0]

    descels = doc.getElementsByTagName('dc:description')
    if descels:
        descel = descels[0]

    metatags = doc.getElementsByTagName('meta')
    for metatag in metatags:
        if metatag.getAttribute('name') == 'calibre:series':
            series = metatag.getAttribute('content')
        elif metatag.getAttribute('name') == 'calibre:series_index':
            series_index = metatag.getAttribute('content')
        elif metatag.getAttribute('name') == 'calibre:title_sort':
            sortel = metatag

    return doc, series, series_index, titleel, sortel, descel


def write_metadata(metadatadoc, metadata_file_dst_path):

    """Writes out the book metadata

        metadatadoc                 minidom doc, doc object from source metadata
        metadata_file_dst_path      pathlib.Path(), full path to destination metadata file

        returns                     None
    """

    # create/truncate the metadata file and write it out
    try:
        with open(metadata_file_dst_path, 'w', encoding='utf8') as docfile:
            metadatadoc.writexml(docfile)
    except OSError as excep:
        logging.warning('Could not (over) write metadata file "%s": %s', metadata_file_dst_path, excep)


def sanitize_filename(sani):

    """Removes illegal characters from strings that will be incorporated in
    file names.

        sani                string to sanitize

        returns             sanitized string

    From:   stackoverflow thread
            https://stackoverflow.com/questions/7406102/create-sane-safe-filename-from-any-unsafe-string
    By:     Mitch McMabers https://stackoverflow.com/users/8874388/mitch-mcmabers and others
    """

    # illegal chars
    sani = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", sani)
    # windows illegal file names
    sani = re.sub(
        r"^ ?(CON|CONIN\$|CONOUT\$|PRN|AUX|CLOCK\$|NUL|"
        r"COM0|COM1|COM2|COM3|COM4|COM5|COM6|COM7|COM8|COM9|"
        r"LPT0|LPT1|LPT2|LPT3|LPT4|LPT5|LPT6|LPT7|LPT8|LPT9|"
        r"LST|KEYBD\$|SCREEN\$|\$IDLE\$|CONFIG\$)([. ]|$)",
        '-', sani, flags=re.IGNORECASE
    )
    # windows illegal chars at start/end
    sani = re.sub(r"^ |[. ]$", '-', sani)

    return sani


def do_book(
    author_folder_dst_path, book_folder_src_path, book_file_types,
    foldermode, jellyfin_store,
    mangle_meta_title, mangle_meta_title_sort
):

    """Creates folder, files and symlinks for one book.

        author_folder_src_path      pathlib.Path, full path to source author folder
        author_folder_dst_path      pathlib.Path, full path to destination author folder
        book_folder_src_path        pathlib.Path, full path to source book folder
        book_file_types             list, extensions identifying book files (exclude periods)
        foldermode                  str, one of 'author,series,book' or 'book'
        jellyfin_store              pathlib.Path, full path top level output storage location
                                    (i.e. will be jellyfin library folder)
        mangle_meta_title           boolean, true if metadata title should be mangled
        mangle_meta_title_sort      boolean, true if metadata sort title should be mangled

        returns                 None
    """

    global CMDARGS

    # find first instance of configured book file types
    book_file_src_path = find_book(book_file_types, book_folder_src_path)
    if not book_file_src_path:
        return
    print(book_folder_src_path, flush=True)

    # locate related book files
    book_folder = book_folder_src_path.name
    metadata_file_src_path = find_metadata(book_folder_src_path)
    cover_file_src_path = find_cover(book_folder_src_path)
    metadatadoc, series, series_index, titleel, sortel, descel = get_metadata(metadata_file_src_path)

    # Output is organized as '.../author/series/book/book.ext' or '.../book/book.ext' depending on foldermode.
    # If series info was expected but not found, output structure collapses to '.../author/book/book.ext'.
    # If series info was expected and found, then mangle the book's folder name by prepending the book's series index.
    # Once the folder structure has been determined, create the destination folder(s) if they do not exist.

    if series > '' and foldermode == 'author,series,book':
        if series_index == '':
            series_index = '99'
        book_folder = sanitize_filename(f'{series_index:>03s} - {book_folder}')
        book_folder_dst_path = author_folder_dst_path / sanitize_filename(f'{series} Series') / book_folder
    elif foldermode == 'book':
        book_folder_dst_path = jellyfin_store / book_folder
    else:
        book_folder_dst_path = author_folder_dst_path / book_folder

    try:
        book_folder_dst_path.mkdir(parents=True, exist_ok=True)
    except OSError as excep:
        logging.warning(
            'Could not create book\'s destination folder (or a parent folder thereof) '
            '"%s": %s', book_folder_dst_path, excep
        )
        if metadatadoc:
            metadatadoc.unlink()
        return

    # copy the book file
    book_file_dst_path = book_folder_dst_path / book_file_src_path.name
    copy_book = False
    if book_file_dst_path.exists():
        if stat(book_file_dst_path).st_mtime < stat(book_file_src_path).st_mtime:
            copy_book = True
    else:
        copy_book = True

    if copy_book:
        try:
            copyfile(book_file_src_path, book_file_dst_path)
        except Exception as excep:
            logging.warning('Could not copy the book file %s: %s', book_file_dst_path, excep)

    # copy the cover image
    if cover_file_src_path is not None:
        cover_file_dst_path = book_folder_dst_path / cover_file_src_path.name
        copy_cover = False
        if cover_file_dst_path.exists():
            if stat(cover_file_dst_path).st_mtime < stat(cover_file_src_path).st_mtime:
                copy_cover = True
        else:
            copy_cover = True

        if copy_cover:
            try:
                copyfile(cover_file_src_path, cover_file_dst_path)
            except Exception as excep:
                logging.warning('Could not copy the cover image %s: %s', cover_file_dst_path, excep)

    # Output a metadata xml (.opf) file into the destination book folder.
    # If folder mode is 'author,series,book', series info was found,
    # and mangling is enabled, mangle the book title (<dc:title>) and/or title_sort
    # elements by prepending the book's index to it's title.
    # Also prepend a "Book X of Lorem Ipsum" header to the book description.
    # Otherwise, write out the original metadata unchanged.

    if metadatadoc:

        metadata_file_dst_path = book_folder_dst_path / metadata_file_src_path.name
        copy_metadata = False

        if CMDARGS.updateAllMetadata:
            copy_metadata = True
        elif metadata_file_dst_path.exists():
            if stat(metadata_file_dst_path).st_mtime < stat(metadata_file_src_path).st_mtime:
                copy_metadata = True
        else:
            copy_metadata = True

        if copy_metadata:
            if series > '' and foldermode == 'author,series,book':
                if titleel and mangle_meta_title:
                    titleel.firstChild.data = f'{series_index:>03s} - {titleel.firstChild.data}'
                if sortel and mangle_meta_title_sort:
                    sortel.setAttribute('content', f'{series_index:>03s} - {sortel.getAttribute("content")}')
                if descel:
                    descel.firstChild.data = f'<H4>Book {series_index} of <em>{series}</em></H4>{descel.firstChild.data}'

            write_metadata(metadatadoc, metadata_file_dst_path)

        metadatadoc.unlink()


def do_construct(section):

    """Create (or update) one target Jellyfin e-book library as defined by a configured Construct section

        section             config parser section obj

        returns             None
    """

    global CONFIG_FILE_PATH

    try:
        # convert multiline configs to lists
        author_folders = section['authorFolders'][1:].split('\n')
        book_file_types = section['bookfiletypes'][1:].split('\n')
        # get simple configs
        calibre_store = Path(section['calibreStore'])
        jellyfin_store = Path(section['jellyfinStore'])
        foldermode = section['foldermode']
        mangle_meta_title = section.getboolean('mangleMetaTitle')
        mangle_meta_title_sort = section.getboolean('mangleMetaTitleSort')
    except Exception as excep:
        logging.critical(
            'A required parameter is missing from %s '
            'in configuration file "%s". : %s',
            section, CONFIG_FILE_PATH, excep
        )
        sys.exit(-1)

    # sanity check configuration parameters
    try:
        if not calibre_store.is_dir():
            raise ValueError(f'calibreStore value "{calibre_store}" is not a directory')
        if not jellyfin_store.is_dir():
            raise ValueError(f'jellyfinStore value "{jellyfin_store}" is not a directory')
        if jellyfin_store.samefile(calibre_store):
            raise ValueError('jellyfinStore and calibreStore must be different locations')
        if foldermode not in ('book', 'author,series,book'):
            raise ValueError('foldermode value must be "book" or "author,series,book"')
        if author_folders[0] == '':
            raise ValueError('authorFolders must contain at least one entry')
        if book_file_types[0] == '':
            raise ValueError('bookfiletypes must contain at least one entry')
    except ValueError as excep:
        logging.critical(
            'Inappropriate parameter value in %s in configuration file "%s": %s',
            section, CONFIG_FILE_PATH, excep
        )
        sys.exit(-1)

    # for each configured author
    for author_folder in author_folders:

        # get and create destination author folder
        author_folder_src_path = calibre_store / author_folder
        author_folder_dst_path = jellyfin_store / author_folder
        if foldermode == 'author,series,book':
            try:
                author_folder_dst_path.mkdir(parents=True, exist_ok=True)
            except OSError as excep:
                logging.warning('Could not create author folder "%s": %s', author_folder_dst_path, excep)
                continue

        # for each book folder in source author folder
        for book_folder_src_path in author_folder_src_path.iterdir():
            do_book(
                author_folder_dst_path, book_folder_src_path,
                book_file_types, foldermode, jellyfin_store,
                mangle_meta_title, mangle_meta_title_sort
            )


# ------------------
#   Main
# ------------------


def main(clargs=None):

    """Main

        clargs                      [], list of command line arguments
                                    used to invoke when/if calibre2jellyfin is loaded as a module
                                    example:
                                    calibre2jellyfin.main(['--update-all-metadata', ...])
    """

    global CMDARGS

    logging.basicConfig(format='%(levelname)s:%(filename)s:%(lineno)s: %(message)s', level=logging.DEBUG)

    # Parse command line arguments
    cmdparser = argparse.ArgumentParser(
        description='A utility to construct a Jellyfin ebook library from a Calibre library.'
        f' Configuration file "{CONFIG_FILE_PATH}" is required.'
    )
    cmdparser.add_argument(
        '--update-all-metadata',
        dest='updateAllMetadata',
        action='store_true',
        help='Useful to force a one-time update of all metadata files, '
        'for instance when configurable metadata mangling options have changed. '
        '(Normally metadata files are only updated when missing or out-of-date.)'
    )
    if clargs:
        CMDARGS = cmdparser.parse_args(clargs)
    else:
        CMDARGS = cmdparser.parse_args()

    # read configuration
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf8') as configfile:
            config = configparser.ConfigParser()
            config.read_file(configfile)
    except OSError as configexcep:
        logging.critical('Could not read configuration "%s": %s', CONFIG_FILE_PATH, configexcep)
        sys.exit(-1)
    except configparser.Error as configexcep:
        logging.critical('Invalid configuration "%s": %s', CONFIG_FILE_PATH, configexcep)
        sys.exit(-1)

    logging.info('Using configuration "%s"', CONFIG_FILE_PATH)

    # Default mangling behavior to that of original script
    config['DEFAULT']['mangleMetaTitle'] = '1'
    config['DEFAULT']['mangleMetaTitleSort'] = '0'

    # for each configured Construct
    for section in config:
        if section[0:9] == 'Construct':
            try:
                do_construct(config[section])
            except Exception as unexpected:
                logging.critical('Unexpected error encountered constructing [%s]: %s', section, unexpected)
                sys.exit(-1)


if __name__ == '__main__':
    main()
