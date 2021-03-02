# -*- coding: utf-8 -*-
import gettext

from common.settings import LANGUAGE, LOCALES_PATH


def lang_init():
    translation = gettext.translation("messages", LOCALES_PATH, languages=[LANGUAGE])
    translation.install()
    return translation.gettext
