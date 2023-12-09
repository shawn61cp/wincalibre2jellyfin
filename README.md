# wincalibre2jellyfin
Python script to construct a Jellyfin ebook library from a Calibre library.

## Windows 
<em>(The Linux version of this script is maintained as a separate project.  Please see [calibre2jellyfin](https://github.com/shawn61cp/calibre2jellyfin)).</em>

#### Overview
* Created folder structure (foldermode in .cfg) is one of:
  * ...\author\series\book\...
  * ...\book\...
* Destination book folder contains
  * copy of book file from Calibre library
  * copy of cover image from Calibre library
  * copy, possibly modified, of Calibre's metadata file
* Books are selected for inclusion by listing author folders in the .cfg file
* Series handling
  * When foldermode is author\series\book, the script will extract series and series index from Calibre's metadata file.  If found, the target book folder name will be prepended with the series index.  So will the \<dc:title\> element in the metadata file.  If series info is expected but not found, the structure collapses to ...\author\book\....
* Multiple output libraries may be configured 

#### Example author/series/book structure 
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
    │   └── Book A.epub
    ├── Book B\
    │   ├── cover.jpg
    │   ├── metadata.opf
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
Jellyfin will display a drillable folder structure similarly to the way it does for movies, shows, and music.  Jellyfin will extract and display the mangled book title that is prepended with the series index as the book title.

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
1. Save the zip file somewhere convenient, your Documents folder is suggessted, and extract it.  We will call this EXTRACT_FOLDER.

#### Usage

* In file explorer, navigate to EXTRACT_FOLDER\wincalibre2jellyfin-main\
* Edit the wincalibre2jellyfin.cfg file before first use.
* Double click on wincalibre2jellyfin.py to run the script


#### Calibre Author Folders

Typically the Calibre author folder is named exactly as the author appears in the Calibre interface.  Occasionally however it is not.  I have seen this when Calibre displays authors as "Jane Doe & John Q. Public" but the folder name is actually just "Jane Doe".  Also when the list of authors is very long, as happens in technical books, Calibre will limit the length of the folder name.

If you find that an expected author does not show up in the created Jellyfin library, double check that the author as listed in the .cfg file matches the actual folder name in the Calibre library.

Another thing I have encountered is when multiple versions of the author name exist, such as "Public, John Q." and "John Q. Public", and they are then consolidated, Calibre actually moves the books into the folder matching the consolidated name.  If the author name configured for calibre2jellyfin happened to match the author name that "went away", updates to that author's books may appear to die, or you might see two different versions of the same author in Jellyfin.  The solution is to just delete, in Jellyfin, one or both authors, ensure that the author configured in the .cfg file matches the Calibre author folder, then re-run the script to have them cleanly re-created.  Jellyfin will eventually detect the changes and update the display contents.  You can also right-click on an item within Jellyfin and request an immediate metadata refresh.  Even so sometimes it will take a few minutes  for Jellyfin to recognize the changes.

