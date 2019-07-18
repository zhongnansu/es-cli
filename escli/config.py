import errno
import os
import platform
import shutil

from os.path import expanduser, exists, dirname
from configobj import ConfigObj


def config_location():
    """Return absolute config file path according to different OS."""
    if "XDG_CONFIG_HOME" in os.environ:
        return "%s/escli/" % expanduser(os.environ["XDG_CONFIG_HOME"])
    elif platform.system() == "Windows":
        return os.getenv("USERPROFILE") + "\\AppData\\Local\\dbcli\\escli\\"
    else:
        return expanduser("~/.config/escli/")


def _load_config(user_config, default_config=None):
    config = ConfigObj()
    config.merge(ConfigObj(default_config, interpolation=False))
    config.merge(
        ConfigObj(expanduser(user_config), interpolation=False, encoding="utf-8")
    )
    config.filename = expanduser(user_config)

    return config


def ensure_dir_exists(path):
    """
    Try to Create config file in OS.

    Raise error if file already exists.
    """
    parent_dir = expanduser(dirname(path))
    try:
        os.makedirs(parent_dir)
    except OSError as exc:
        # ignore existing destination (py2 has no exist_ok arg to makedirs)
        if exc.errno != errno.EEXIST:
            raise


def _write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    ensure_dir_exists(destination)

    shutil.copyfile(source, destination)


def get_config(esclirc_file=None):
    """
    Get config for escli.

    This config comes from either existing config in the OS, or create a config file in the OS, and write default config
    including in the package to it.
    """
    from escli import __file__ as package_root

    package_root = os.path.dirname(package_root)

    esclirc_file = esclirc_file or "%sconfig" % config_location()

    default_config = os.path.join(package_root, "esclirc")
    _write_default_config(default_config, esclirc_file)

    return _load_config(esclirc_file, default_config)
