##########################################
from settings import LANGUAGE

import locale
import gettext

def lang_init():
    _encoding = locale.getdefaultlocale()  # Default system values

    lang = gettext.translation('messages', 'locales/', languages=[LANGUAGE])
    lang.install()
    return lang.gettext
###########################################