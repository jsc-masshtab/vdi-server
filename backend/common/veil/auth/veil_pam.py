# -*- coding: utf-8 -*-

try:
    from veil_aio_au import VeilAuthPam
except ImportError:
    VeilAuthPam = None

from common.settings import (PAM_AUTH,
                             PAM_USER_SET_PASS_CMD,
                             PAM_USER_REMOVE_CMD,
                             PAM_USER_EDIT_CMD,
                             PAM_CHECK_IN_GROUP_CMD,
                             PAM_USER_ADD_CMD,
                             PAM_GROUP_ADD_CMD,
                             PAM_TASK_TIMEOUT,
                             PAM_SUDO_CMD,
                             PAM_KILL_PROC_CMD)

if PAM_AUTH and VeilAuthPam:
    veil_auth_class = VeilAuthPam(
        task_timeout=PAM_TASK_TIMEOUT,
        user_add_cmd=PAM_USER_ADD_CMD,
        group_add_cmd=PAM_GROUP_ADD_CMD,
        user_edit_cmd=PAM_USER_EDIT_CMD,
        user_set_pass_cmd=PAM_USER_SET_PASS_CMD,
        user_check_in_group_cmd=PAM_CHECK_IN_GROUP_CMD,
        user_remove_group_cmd=PAM_USER_REMOVE_CMD,
        sudo_cmd=PAM_SUDO_CMD,
        kill_cmd=PAM_KILL_PROC_CMD
    )
else:
    veil_auth_class = None
