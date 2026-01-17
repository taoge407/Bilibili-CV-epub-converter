# Bilibili Readlist-epub converter
## To-Do List
1. ⬛ Support single article.
2. ⬛ Offer more content source(such as other websites?)
3. ✅ Save cache file to decrease network pressure
4. ✅ Fix images reference, now you can see pictures and cover in ebook.

## How to use?
1. Clone this repo.

    `git clone https://github.com/taoge407/Bilibili-CV-epub-converter.git`
2. Install all the libs required.
    
    `pip install -r requirements.txt`
3. Run the script.

    `python converter.py <readlist ID without perfix>`
    Eg: `python converter.py 36436`
4. The epub file will be generated in the running dir.
5. If sometimes cookies are required, paste your cookies in the file `cookie.txt` in the working dir

    Eg: buvid3=143159......; b_nut=xxxxx; b_lsid=xxx; _uuid=xxxxx