##########################################
from settings import LANGUAGE

import gettext


def lang_init():
    lang = gettext.translation('messages', '../locales/', languages=[LANGUAGE])
    lang.install()
    return lang.gettext
