# wincalibre2jellyfin
Python script to construct a Jellyfin ebook library from a Calibre library.

## Windows 
<em>(The Linux version of this script is maintained as a separate project.  Please see [calibre2jellyfin](https://github.com/shawn61cp/calibre2jellyfin)).</em>

#### Overview
* Created folder structure (foldermode in .cfg) is one of:
  * .../author/series/book/...
  * .../series/book/...
  * .../book/...
* Destination book folder contains
  * symlink to (single) book file in Calibre library (based on configured order of preference)
  * symlink to cover image in Calibre library
  * copy, possibly modified, of Calibre's metadata file
* Books may be selected in the .cfg file by author folder or by subject.
  * Allows you to exclude from Jellyfin those messy persistent remnants from the years when your library was scattered over multiple proprietary platforms.
  * Allows you to separate differing levels of mature content into separate Jellyfin libraries, access to which can be restricted within Jellyfin.  (See Real Life section below for further discussion.)
  * Allows you to dispose books into libraries with differing structures as called out below in <em>Series Handling</em>
* Alternatively all books in the source library may be exported.
* Series handling
  * Foldermode is author/series/book
    * <em>Suitable for fiction libraries</em>
    * The script will attempt to extract series and series index from Calibre's metadata file.
    * If found, the target book folder name will be prepended with the series index.  Optionally, the metadata \<dc:title\> and the \<meta name="calibre:title_sort" content="...sort title..."\> may be treated in the same way.
    * A short header identifying the index and series is prepended to the book description.
    * If series info is expected but not found, the structure collapses to .../author/book/.... and no mangling is performed.
  * Foldermode is series/book
    * <em>Suitable for eComic libraries</em>
    * This mode is similar to author/series/book above except there is no grouping by author, only by series and book, unless the series info is missing in which case the structure collapses to .../book/...
  * Foldermode is book
    * <em>Suitable for non-fiction libraries</em>
    * Books are organized strictly by book title
* Multiple output libraries may be configured 

#### Example author/series/book structure 
_Example assumes script has been configured to prefer .epub types over .azw and .mobi._
<table>
  <thead>
    <tr><th>Calibre store</th><th>Created Jellyfin store</th></tr>
  </thead>
 <tbody>
  <tr>
   <td><pre>
└── Author\
    └── Book A\
    │   ├── cover.jpg
    │   ├── metadata.opf
    │   ├── Book A.azw
    │   └── Book A.epub
    ├── Book B\
    │   ├── cover.jpg
    │   ├── metadata.opf
    │   ├── Book B.mobi
    │   └── Book B.epub
   </pre>
   </td>
   <td><pre>
└── Author\
    └── Lorem ipsum dolor sit amet Series\
        ├── 001 - Book A\
        │   ├── cover.jpg      <- copy
        │   ├── metadata.opf   <- modified copy
        │   └── Book A.epub    <- copy
        ├── 002 - Book B\
        │   ├── cover.jpg      <- copy
        │   ├── metadata.opf   <- modified copy
        │   └── Book B.epub    <- copy
   </pre>    
   </td>
  </tr>
 </tbody>
</table>
Jellyfin will display a drillable folder structure similarly to the way it does for movies, shows, and music.  Jellyfin will extract, display, and sort by the mangled book title that is prepended with the series index.

#### Example series/book structure
_The "series/book" option is intended for use with eComics, thanks for this go to [Cudail](https://github.com/cudail)._
<table>
  <thead>
    <tr><th>Calibre store</th><th>Created Jellyfin store</th></tr>
  </thead>
 <tbody>
  <tr>
   <td><pre>
└── Author M\
    └── Comic A\
        ├── cover.jpg
        ├── metadata.opf
        └── Comic A.cbz
└── Author N\
    └── Comic B\
        ├── cover.jpg
        ├── metadata.opf
        └── Comic B.cbz
   </pre>
   </td>
   <td><pre>
└── Lorem ipsum dolor sit amet Series/
    ├── 001 - Comic A\
    │   ├── cover.jpg      <- copy
    │   ├── metadata.opf   <- modified copy
    │   └── Comic A.cbz    <- copy
    ├── 002 - Comic B\
    │   ├── cover.jpg      <- copy
    │   ├── metadata.opf   <- modified copy
    │   └── Comic B.cbz    <- copy
   </pre>    
   </td>
  </tr>
 </tbody>
</table>

#### Changes
* 2024-11-22 (Current version) (Main branch)
  * Added support for selection of all books in the source library
  * Added support for Selection of books by subject (aka tags in Calibre)
  * Added command line options
    * -\-dryrun
      * This displays normal console output plus showing where files would be output but does not actually export anything.
    * -\-debug
      * Displays lots of path and metadata information.  Useful if you need to look into why a book is or is not being selected.
    * -\-version
    * -\-list LIST_SPEC
      * Outputs a report that can be useful in curating your library.
  * New configurations (see example .cfg)
    * selectionMode = [author | subject | all]
    * subjects = ...
  * Additional warnings
    * Missing cover file
    * Missing metadata file
        * Note: In 'subject' selection mode, if the metadata is missing the book cannot be exported.
  * All authors now appear in the description header and the authors by-line appears in all folder modes whether there is series info or not.
    * Run once with --update-all-metadata to apply
  * Upgrade considerations
    * If you already have the 2024-09-02 version and are not interested in selection by subject, there is not much reason to download this version.  The selection by author functionality has not changed.
    * If you download this version because you are interested in the new warnings or the new command line options but not selection by subject or selection of all books, you do not need to make any changes to your configuration file.  Behavior defaults to selection by author.
    * If you are interested in selection by subject, you will need to add the selectionMode and subjects parameters to your configuration file.  In 'author' or 'all' selectionMode, any subjects list is ignored.  In 'subject' or 'all' selectionMode, any authors list is ignored.  You can maintain both lists and switch between them using selectionMode.
    * If you are interested in selection of all books, you will need to add just the selectionMode parameter.
* 2024-09-02
    * Add author's name to book description.
    * Add support for fractional series indices maintaining sort
        * ''          ->  '999'
        * '3'         ->  '003'
        * '34'        ->  '034'
        * '345'       ->  '345'
        * '3456'      ->  '3456'
        * '3.2'       ->  '003.02'    <- new
        * Notes
            * Any series books that had fractional indices prior to this version will appear as new book folders with the index formatted in the new way and leaving the prior formatted versions as duplicates.  You will probably want to delete, in Jellyfin, the old versions.
    * Add warning when book file of configured type not found in book folder
* 2024-06-19
    * Add support for "series/book" mode, thanks to [Cudail](https://github.com/cudail)
* 2024-02-21
    * Coding/style improvements and lint cleanup only.  No functional changes.  If you already have the 2024-01-27 version installed there is no real reason to download this version.
* 2024-01-27
    * Add support for mangling the metadata title sort value
    * Make metadata mangling behavior configurable (new configuration parameters)
        * mangleMetaTitle = [1 | 0]
        * mangleMetaTitleSort = [1 | 0]
    * Add command line option to force update of all metadata files.
        * -\-update-all-metadata

#### Dependencies

* Python 3
    1. In your browser, navigate to [python.org](https://www.python.org/)
    1. In the main menu, hover over "Download".
    1. In the resulting drop down, click on "Windows".
    1. In the first release under the heading "Stable Releases", click on "Windows Installer (64-bit)".  Save the file to your Downloads folder and run it.  This installs Python 3 under your user account.
  
#### Installation

1. In your browser navigate to "https://github.com/shawn61cp/wincalibre2jellyfin"
1. Click the green "Code" button
1. In the resulting dropdown, just over halfway down, find and click on "Download ZIP".
1. Save the zip file somewhere convenient, your Documents folder is suggested, and extract it.  We will call this EXTRACT_FOLDER.

#### Usage

* In file explorer, navigate to EXTRACT_FOLDER\wincalibre2jellyfin-main\
* Edit the wincalibre2jellyfin.cfg file before first use.
* Double click on wincalibre2jellyfin.py to run the script


#### Upgrading

Two things need to be accomplished:
1. Replace your current script, wherever it was originally installed, with the new one.
    * This can be done basically by following the installation steps but you may need to extract the new zip file to a location other than the one you used originally in order to ensure that your existing configuration is not destroyed.  Once the new zip file is extracted safely, you can copy only the new script over the top of the original script.
1. Add any new config options to your existing configuration file.
    * This can be done by copying and pasting any new configuration parameters from the new sample configuration into your current configuration, or even just editing your current configuration.  New configuration options are listed in the *Changes* section and also in the sample .cfg file.

#### Command line  options
<pre>
usage: calibre2jellyfin.py [-h] [--debug] [--dryrun] [--list LIST_SPEC]
                           [--update-all-metadata] [-v]

A utility to construct a Jellyfin ebook library from a Calibre library. Configuration file "wincalibre2jellyfin.cfg" is required.

options:
  -h, --help             show this help message and exit
                         
  --debug                Emit debug information.
                         
  --dryrun               Displays normal console output but makes no changes to
                         exported libraries.
                         
  --list LIST_SPEC       Suspends normal export behavior. Instead prints info
                         from configuration sections and file system that is
                         useful for curation. LIST_SPEC is a comma-delimited
                         list of columns to include in the report. The output
                         is tab-separated. Columns may be one or more of
                         author, section, book, bfolder, afolder, or subject.
                         author: display author name if the source folder
                         exists. section: display section name. book: display
                         book title. bfolder: display book folder. afolder:
                         display author folder. subject: display subject that
                         matched. The report output is sorted so there will be
                         a pause while all configured sections are processed.
                         
  --update-all-metadata  Useful to force a one-time update of all metadata
                         files, for instance when configurable metadata
                         mangling options have changed. (Normally metadata
                         files are only updated when missing or out-of-date.)
                         
  -v, --version          Display version string.
</pre>

## Real Life

The installation and usage instructions above work fine but other situations may be encountered or other conveniences desired.

### Calibre Author Folders

Typically the Calibre author folder is named exactly as the author appears in the Calibre interface.  Occasionally however it is not.  I have seen this when Calibre displays authors as "Jane Doe & John Q. Public" but the folder name is actually just "Jane Doe".  Also when the list of authors is very long, as happens in technical books, Calibre will limit the length of the folder name.

If you find that an expected author does not show up in the created Jellyfin library, double check that the author as listed in the .cfg file matches the actual folder name in the Calibre library.

Another thing I have encountered is when multiple versions of the author name exist, such as "Public, John Q." and "John Q. Public", and they are then consolidated, Calibre actually moves the books into the folder matching the consolidated name.  If the author name configured for calibre2jellyfin happened to match the author name that "went away", updates to that author's books may appear to die, or you might see two different versions of the same author in Jellyfin.  The solution is to just delete, in Jellyfin, one or both authors, ensure that the author configured in the .cfg file matches the Calibre author folder, then re-run the script to have them cleanly re-created.  Jellyfin will eventually detect the changes and update the display contents.  You can also right-click on an item within Jellyfin and request an immediate metadata refresh.  Even so sometimes it will take a few minutes  for Jellyfin to recognize the changes.

### Tricks with \[Construct\] jellyfinStore

Although the instructions in the example .cfg file state categorically that the jellyfinStore parameter should be set to the location of the Jellyfin library, there actually is some wiggle room.

Suppose that you want top level folders in your Jellyfin library that separate your fiction library into "Science Fiction", "Fantasy", "Westerns", and "Romance".  You could create the following structure for the Jellyfin library and then create separate \[Construct\] sections for each top level category.

<pre>
...\fiction\                <- point the Jellyfin library here
    ├── Fantasy\            <- point a [ConstructFantasy] jellyfinStore param here
    ├── Romance\            <- point a [ConstructRomance] jellyfinStore param here
    ├── Science Fiction\    <- point a [ConstructSciFi] jellyfinStore param here
    └── Westerns\           <- point a [ConstructWesterns] jellyfinStore param here
</pre>

Then using your desired selectionMode, arrange for appropriate books to be output from each \[Construct...\] section.  Jellyfin would then display drillable category folders above the author folders (or whatever folderMode you choose).

### Mature Content

Selection by author, although good for this purpose, is not exactly 100% perfect since it is possible for a single author to write content of differing level.

Selection by subject gives finer grained control but tags are often missing and when present seem inconsistent.  To really make selection-by-subject work you would probably have to curate tags yourself.

Another approach would be to combine construction methods.  Nothing prevents having multiple \[Construct\] sections that output to the same Jellyfin library.  (You probably would want to use the same foldermode.) One could exclude problematic authors (No offense, authors!) from a selection-by-author \[Construct\] and then handle those within a selection-by-subject \[Construct\].

### Curation

#### Prerequisites

The reports described here require the sqlite3 command shell and a couple unix utilities.  To install them follow these instructions.

* Sqlite3
  * Create a folder in which to install the sqlite utilities.  This example will use <code>C:\sqlite</code>.
  * Download the sqlite-tools-win-x64-nnnnnnn.zip file from the <em>Precompiled Binaries for Windows</em> section at [https://sqlite.org/download.html](https://sqlite.org/download.html) into <code>C:\sqlite</code> and extract it there.  It's always a good idea to run a virus scan on anything downloaded from the internet and to verify the listed checksum.
  * Add <code>C:\sqlite</code> to your PATH
    * Click the start button, search for and click <code>edit the system environment variables</code>.
    * Click <code>Environment Variables</code> at the bottom of the dialog.
    * Click <code>Path</code> in the system variables section, then click <code>Edit</code>.  (The system path makes it available to all users.)
    * Click <code>New</code>, enter <code>C:\sqlite</code> and press Enter.
    * Click <code>OK</code> to complete and exit all three dialogs.
  * sqlite3 will now be runnable from a cmd prompt.
* Unix Utils
  * Create a folder in which to install the unix utilities.  This example will use <code>C:\unxutils</code>.
  * Download the UnxUtils zip file from [https://sourceforge.net/projects/unxutils/](https://sourceforge.net/projects/unxutils/) into <code>C:\unxutils</code> and extract it there.  You can find the checksums in the Files tab in unxutils/current. Click on the (i) info button.
  * Add <code>C:\unxutils\usr\local\wbin</code> to your PATH
    * Click the start button, search for and click <code>edit the system environment variables</code>.
    * Click <code>Environment Variables</code> at the bottom of the dialog.
    * Click <code>Path</code> in the system variables section, then click <code>Edit</code>.  (The system path makes it available to all users.)
    * Click <code>New</code>, enter <code>C:\unxutils\usr\local\wbin</code> and press Enter.
    * Click <code>OK</code> to complete and exit all three dialogs.
  * Several of the standard Linux / Unix utilities will now be runnable from a cmd prompt.  We are interested in the <code>cat</code>, <code>uniq</code>, and <code>less</code> utilities.

#### Listing Calibre author folders that will <em>not</em> be output by calibre2jellyfin.

Step 1 - Get a list of author folders in the Calibre library.

<code>dir /b "PATH_TO_CALIBRE_LIBRARY" >afolders_c</code>

Step 2 - Get a list of author folders that calibre2jellyfin is exporting.

<code>"PATH_TO_WINCALIBRE2JELLYFIN.PY\wincalibre2jellyfin.py" --list afolder >afolders_jf</code>

Step 3 - Construct a list of folders that only exist in one but not both of the lists.  Absent something strange having occurred, there cannot be folders output by calibre2jellyfin that do not exist in the Calibre library, so this leaves only those Calibre library folders that will not be exported.

<code>cat afolders_c afolders_jf | sort | uniq -u >afolders_todo</code>

Step 4 - Review the list.  Note that there are a small number of files in the Calibre library such as the metadata.db that will appear in this list.  It seems easier to just ignore them rather than taking the trouble to filter them out.

<code>less afolders_todo</code>

#### Compact list of Calibre author's series

<strong><em><ins>Caveat Usor:</ins></em></strong> The following uses sqlite3 to access the Calibre metadata database directly.  Read-only select statements should not present problems.  Nevertheless it is a good idea to make a backup of such an important file.

<pre>sqlite3 -column "PATH_TO_CALIBRE_LIBRARY\metadata.db" "select A.name as author, S.name as series from authors A inner JOIN books_authors_link BAL on BAL.author = A.id inner JOIN books_series_link BSL on BSL.book = BAL.book inner JOIN series S on  S.id = BSL.series group by A.name, S.name order by 1, 2 ;"|less -S</pre>

#### Compact list of Calibre author's books

<strong><em><ins>Caveat Usor:</ins></em></strong> The following uses sqlite3 to access the Calibre metadata database directly.  Read-only select statements should not present problems.  Nevertheless it is a good idea to make a backup of such an important file.

<pre>sqlite3 -column "PATH_TO_CALIBRE_LIBRARY\metadata.db" "select A.name as author, B.title as book, coalesce(S.name, '') as series from authors A inner join books_authors_link BAL on  BAL.author = A.id inner join books B on B.id = BAL.book left join books_series_link BSL on  BSL.book = B.id left join series S on S.id = BSL.series order by 1, 2;"|less -S</pre>

#### Compact list of Calibre collaborator's books

<strong><em><ins>Caveat Usor:</ins></em></strong> The following uses sqlite3 to access the Calibre metadata database directly.  Read-only select statements should not present problems.  Nevertheless it is a good idea to make a backup of such an important file.

<pre>sqlite3 -column "PATH_TO_CALIBRE_LIBRARY\metadata.db" "select (select group_concat(A.name, ',') from books_authors_link BAL inner join authors A on  A.id = BAL.author where BAL.book = B.id) as author, B.title as book, coalesce(S.name, '') as series from books B left join books_series_link BSL on BSL.book = B.id left join series S on  S.id = BSL.series order by 1, 2;"|less -S</pre>

## Odds and Ends

* I have noticed that Jellyfin does not re-paginate if you resize the browser window or change the zoom factor <em>after</em> you have opened the book.  However if you do these <em>before</em> opening the book it does so nicely.
