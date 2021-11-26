from setuptools import setup
from setuptools.command.install import install
import warnings


# Set up the machinery to install custom fonts.  Subclass the setup tools install
# class in order to run custom commands during installation.
class move_ttf(install):
    def run(self):
        """
        Performs the usual install process and then copies the True Type fonts
        that come with clearplot into matplotlib's True Type font directory,
        and deletes the matplotlib fontList.cache
        """
        # Perform the usual install process
        install.run(self)
        # Try to install custom fonts
        #try:
        print("WOWOWOW")
        import os, shutil
        import matplotlib as mpl

        # Find where matplotlib stores its True Type fonts
        mpl_data_dir = os.path.dirname(mpl.matplotlib_fname())
        mpl_ttf_dir = os.path.join(mpl_data_dir, 'fonts', 'ttf')

        # Copy the font files to matplotlib's True Type font directory
        for font in os.listdir("assets/fonts"):
            old_path = os.path.join("assets/fonts", font)
            new_path = os.path.join(mpl_ttf_dir, font)
            shutil.copyfile(old_path, new_path)

        # Try to delete matplotlib's fontList cache
        mpl_cache_dir = mpl.get_cachedir()
        mpl_cache_dir_ls = os.listdir(mpl_cache_dir)

        for file in mpl_cache_dir_ls:
            if file[:8] + file[-5:] == "fontlist.json":
                fontList_path = os.path.join(mpl_cache_dir, file)
                os.remove(fontList_path)
        #except:
            #warnings.warn("WARNING: An issue occured while installing the custom fonts for wrappedify.")
