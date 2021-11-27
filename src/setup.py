import os, shutil
import matplotlib as mpl


def setup() -> None:
    mpl_data_dir = os.path.dirname(mpl.matplotlib_fname())
    mpl_ttf_dir = os.path.join(mpl_data_dir, 'fonts', 'ttf')

    # Copy the font files to matplotlib's True Type font directory
    for font in os.listdir("assets/fonts"):
        old_path = os.path.join("assets/fonts", font)
        new_path = os.path.join(mpl_ttf_dir, font)
        shutil.copyfile(old_path, new_path)

    # Getting matplotlib's cache and removing
    mpl_cache_dir = mpl.get_cachedir()
    mpl_cache_dir_ls = os.listdir(mpl_cache_dir)

    for file in mpl_cache_dir_ls:
        if file[:8] + file[-5:] == "fontlist.json":
            fontList_path = os.path.join(mpl_cache_dir, file)
            os.remove(fontList_path)