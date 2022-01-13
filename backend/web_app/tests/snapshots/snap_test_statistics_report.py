# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_group_list 1'] = {
    'web_statistics_report': '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="ru">
<head>
<meta name="generator" content="AWStats 7.5 (build 20160301) from config file awstats.vdi.conf (http://www.awstats.org)">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="content-type" content="text/html; charset=utf-8">
<meta http-equiv="description" content="Awstats - Advanced Web Statistics for vdi (2021-10) - main">
<title>Статистика за vdi (2021-10) - main</title>
<style type="text/css">
body { font: 11px verdana, arial, helvetica, sans-serif; background-color: #FFFFFF; margin-top: 0; margin-bottom: 0; }
.aws_bodyl  { }
.aws_border { border-collapse: collapse; background-color: #CCCCDD; padding: 1px 1px 1px 1px; margin-top: 0px; margin-bottom: 0px; }
.aws_title  { font: 13px verdana, arial, helvetica, sans-serif; font-weight: bold; background-color: #CCCCDD; text-align: center; margin-top: 0; margin-bottom: 0; padding: 1px 1px 1px 1px; color: #000000; }
.aws_blank  { font: 13px verdana, arial, helvetica, sans-serif; background-color: #FFFFFF; text-align: center; margin-bottom: 0; padding: 1px 1px 1px 1px; }
.aws_data {
\tbackground-color: #FFFFFF;
\tborder-top-width: 1px;
\tborder-left-width: 0px;
\tborder-right-width: 0px;
\tborder-bottom-width: 0px;
}
.aws_formfield { font: 13px verdana, arial, helvetica; }
.aws_button {
\tfont-family: arial,verdana,helvetica, sans-serif;
\tfont-size: 12px;
\tborder: 1px solid #ccd7e0;
\tbackground-image : url(/awstatsicons/other/button.gif);
}
th\t\t{ border-color: #ECECEC; border-left-width: 0px; border-right-width: 1px; border-top-width: 0px; border-bottom-width: 1px; padding: 1px 2px 1px 1px; font: 11px verdana, arial, helvetica, sans-serif; text-align:center; color: #000000; }
th.aws\t{ border-color: #ECECEC; border-left-width: 0px; border-right-width: 1px; border-top-width: 0px; border-bottom-width: 1px; padding: 1px 2px 1px 1px; font-size: 13px; font-weight: bold; }
td\t\t{ border-color: #ECECEC; border-left-width: 0px; border-right-width: 1px; border-top-width: 0px; border-bottom-width: 1px; font: 11px verdana, arial, helvetica, sans-serif; text-align:center; color: #000000; }
td.aws\t{ border-color: #ECECEC; border-left-width: 0px; border-right-width: 1px; border-top-width: 0px; border-bottom-width: 1px; font: 11px verdana, arial, helvetica, sans-serif; text-align:left; color: #000000; padding: 0px;}
td.awsm\t{ border-left-width: 0px; border-right-width: 0px; border-top-width: 0px; border-bottom-width: 0px; font: 11px verdana, arial, helvetica, sans-serif; text-align:left; color: #000000; padding: 0px; }
b { font-weight: bold; }
a { font: 11px verdana, arial, helvetica, sans-serif; }
a:link    { color: #0011BB; text-decoration: none; }
a:visited { color: #0011BB; text-decoration: none; }
a:hover   { color: #605040; text-decoration: underline; }
.currentday { font-weight: bold; }
</style>
</head>

<body style="margin-top: 0px">
<a name="top"></a>



<a name="menu">&nbsp;</a>
<form name="FormDateFilter" action="/awstats/awstats.pl?config=vdi&amp;update" style="padding: 0px 0px 20px 0px; margin-top: 0">
<table class="aws_border" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td>
<table class="aws_data sortable" border="0" cellpadding="1" cellspacing="0" width="100%">
<tr><td class="aws" valign="middle"><b>Статистика за:</b>&nbsp;</td><td class="aws" valign="middle"><span style="font-size: 14px;">vdi</span></td><td align="right" rowspan="3"><a href="http://www.awstats.org" target="awstatshome"><img src="/awstatsicons/other/awstats_logo6.png" border="0" alt=\'Awstats Web Site\' title=\'Awstats Web Site\' /></a></td></tr>
<tr valign="middle"><td class="aws" valign="middle" width="150"><b>Последнее обновление:</b>&nbsp;</td><td class="aws" valign="middle"><span style="font-size: 12px;">27 Окт 2021 - 09:44</span></td></tr>
<tr><td class="aws" valign="middle"><b>Отчетный период:</b></td><td class="aws" valign="middle"><span style="font-size: 14px;">Месяц Окт 2021</span></td></tr>
</table>
</td></tr></table>
</form><br />

<table>
<tr><td class="awsm" width="150" valign="top"><b>Когда:</b></td>
<td class="awsm"><a href="#month">История за месяц</a> &nbsp; <a href="#daysofmonth">День месяца</a> &nbsp; <a href="#daysofweek">День недели</a> &nbsp; <a href="#hours">Часы</a> &nbsp; </td></tr>
<tr><td class="awsm" width="150" valign="top"><b>Кто:</b></td>
<td class="awsm"><a href="#countries">Страны</a> &nbsp; <a href="awstats.vdi.alldomains.html" target="awstatsbis">Полный список</a>
 &nbsp; <a href="#visitors">Хосты</a> &nbsp; <a href="awstats.vdi.allhosts.html" target="awstatsbis">Полный список</a>
 &nbsp; <a href="awstats.vdi.lasthosts.html" target="awstatsbis">Последний визит</a>
 &nbsp; <a href="awstats.vdi.unknownip.html" target="awstatsbis">Неразрешенный IP адрес</a>
 &nbsp; <a href="#robots">Роботы/Пауки посетители</a> &nbsp; <a href="awstats.vdi.allrobots.html" target="awstatsbis">Полный список</a>
 &nbsp; <a href="awstats.vdi.lastrobots.html" target="awstatsbis">Последний визит</a>
 &nbsp; </td></tr>
<tr><td class="awsm" valign="top"><b>Навигация:</b></td>
<td class="awsm"><a href="#sessions">Продолжительность визитов</a> &nbsp; <a href="#filetypes">Тип файла</a> &nbsp; <a href="#downloads">Downloads</a> &nbsp; <a href="awstats.vdi.downloads.html" target="awstatsbis">Полный список</a>
 &nbsp; <a href="#urls">Просмотров</a>
 &nbsp; <a href="awstats.vdi.urldetail.html" target="awstatsbis">Полный список</a>
 &nbsp; <a href="awstats.vdi.urlentry.html" target="awstatsbis">Вхождение</a>
 &nbsp; <a href="awstats.vdi.urlexit.html" target="awstatsbis">Выход</a>
 &nbsp; <a href="#os">Операционные системы</a> &nbsp; <a href="awstats.vdi.osdetail.html" target="awstatsbis">Версии</a>
 &nbsp; <a href="awstats.vdi.unknownos.html" target="awstatsbis">Неизвестный</a>
 &nbsp; <a href="#browsers">Браузеры</a> &nbsp; <a href="awstats.vdi.browserdetail.html" target="awstatsbis">Версии</a>
 &nbsp; <a href="awstats.vdi.unknownbrowser.html" target="awstatsbis">Неизвестный</a>
 &nbsp; </td></tr>
<tr><td class="awsm" width="150" valign="top"><b>Рефереры:</b></td>
<td class="awsm"><a href="#referer">Происхождение</a> &nbsp; <a href="awstats.vdi.refererse.html" target="awstatsbis">Ссылающиеся поисковые машины</a>
 &nbsp; <a href="awstats.vdi.refererpages.html" target="awstatsbis">Ссылающиеся сайты</a>
 &nbsp; <a href="#keys">Поиск</a> &nbsp; <a href="awstats.vdi.keyphrases.html" target="awstatsbis">Поисковые&nbsp;Ключевые фразы</a>
 &nbsp; <a href="awstats.vdi.keywords.html" target="awstatsbis">Поисковые&nbsp;Ключевые слова</a>
 &nbsp; </td></tr>
<tr><td class="awsm" width="150" valign="top"><b>Остальные:</b></td>
<td class="awsm"><a href="#misc">Смешанные</a> &nbsp; <a href="#errors">Статусы ошибок HTTP</a> &nbsp; <a href="awstats.vdi.errors400.html" target="awstatsbis">Ошибка&nbsp;Хиты (400)</a>
 &nbsp; <a href="awstats.vdi.errors403.html" target="awstatsbis">Ошибка&nbsp;Хиты (403)</a>
 &nbsp; <a href="awstats.vdi.errors404.html" target="awstatsbis">Ошибка&nbsp;Хиты (404)</a>
 &nbsp; </td></tr>
</table>
<br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Общее </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><td class="aws"><b>Отчетный период</b></td><td class="aws" colspan="5">
Месяц Окт 2021</td></tr>
<tr bgcolor="#ECECEC"><td class="aws"><b>Первый визит</b></td>
<td class="aws" colspan="5">26 Окт 2021 - 10:29</td></tr>
<tr bgcolor="#ECECEC"><td class="aws"><b>Последний визит</b></td>
<td class="aws" colspan="5">27 Окт 2021 - 09:43</td>
</tr>
<tr><td bgcolor="#CCCCDD">&nbsp;</td><td width="17%" bgcolor="#FFAA66">Уникальные посетители</td><td width="17%" bgcolor="#F4F090">Количество визитов</td><td width="17%" bgcolor="#4477DD">Страницы</td><td width="17%" bgcolor="#66DDEE">Хиты</td><td width="17%" bgcolor="#2EA495">Объем</td></tr>
<tr><td class="aws">Отображаемый трафик&nbsp;*</td><td><b>2</b><br />&nbsp;</td><td><b>6</b><br />(3&nbsp;Визитов/Посетитель)</td><td><b>660</b><br />(110&nbsp;Страницы/Визит)</td><td><b>1,010</b><br />(168.33&nbsp;Хиты/Визит)</td><td><b>7.42 МБ</b><br />(1266.11&nbsp;КБ/Визит)</td></tr>
<tr><td class="aws">Не отображаемый трафик&nbsp;*</td><td colspan="2">&nbsp;<br />&nbsp;</td>
<td><b>2</b></td><td><b>11</b></td><td><b>16.85 КБ</b></td></tr>
</table></td></tr></table><span style="font: 11px verdana, arial, helvetica;">* Не отображаемый трафик влючает в себя трафик сгенерированный роботами, вирусами или ответом сервера со специальным HTTP кодом.</span><br />
<br />

<a name="month">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">История за месяц </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr><td align="center">
<center>
<table>
<tr valign="bottom"><td>&nbsp;</td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="31" width="6" alt=\'Уникальные посетители: 2\' title=\'Уникальные посетители: 2\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="91" width="6" alt=\'Количество визитов: 6\' title=\'Количество визитов: 6\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="59" width="6" alt=\'Страницы: 660\' title=\'Страницы: 660\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="91" width="6" alt=\'Хиты: 1010\' title=\'Хиты: 1010\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="91" width="6" alt=\'Объем: 7.42 МБ\' title=\'Объем: 7.42 МБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vu.png" height="1" width="6" alt=\'Уникальные посетители: 0\' title=\'Уникальные посетители: 0\' /><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="6" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td>&nbsp;</td></tr>
<tr valign="middle"><td>&nbsp;</td><td>Янв<br />2021</td><td>Фев<br />2021</td><td>Мар<br />2021</td><td>Апр<br />2021</td><td>Май<br />2021</td><td>Июн<br />2021</td><td>Июл<br />2021</td><td>Авг<br />2021</td><td>Сен<br />2021</td><td>Окт<br />2021</td><td>Ноя<br />2021</td><td>Дек<br />2021</td><td>&nbsp;</td></tr>
</table>
<br />
<table>
<tr><td width="80" bgcolor="#ECECEC">Месяц</td><td width="80" bgcolor="#FFAA66">Уникальные посетители</td><td width="80" bgcolor="#F4F090">Количество визитов</td><td width="80" bgcolor="#4477DD">Страницы</td><td width="80" bgcolor="#66DDEE">Хиты</td><td width="80" bgcolor="#2EA495">Объем</td></tr>
<tr><td>Янв 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Фев 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Мар 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Апр 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Май 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Июн 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Июл 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Авг 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Сен 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Окт 2021</td><td>2</td><td>6</td><td>660</td><td>1,010</td><td>7.42 МБ</td></tr>
<tr><td>Ноя 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Дек 2021</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td bgcolor="#ECECEC">Всего</td><td bgcolor="#ECECEC">2</td><td bgcolor="#ECECEC">6</td><td bgcolor="#ECECEC">660</td><td bgcolor="#ECECEC">1,010</td><td bgcolor="#ECECEC">7.42 МБ</td></tr>
</table>
<br />
</center>
</td></tr>
</table></td></tr></table><br />


<a name="when">&nbsp;</a>

<a name="daysofmonth">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">День месяца </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr><td align="center">
<center>
<table>
<tr valign="bottom">
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="91" width="4" alt=\'Количество визитов: 5\' title=\'Количество визитов: 5\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="62" width="4" alt=\'Страницы: 567\' title=\'Страницы: 567\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="91" width="4" alt=\'Хиты: 835\' title=\'Хиты: 835\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="91" width="4" alt=\'Объем: 6.56 МБ\' title=\'Объем: 6.56 МБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="19" width="4" alt=\'Количество визитов: 1\' title=\'Количество визитов: 1\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="11" width="4" alt=\'Страницы: 93\' title=\'Страницы: 93\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="19" width="4" alt=\'Хиты: 175\' title=\'Хиты: 175\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="12" width="4" alt=\'Объем: 878.40 КБ\' title=\'Объем: 878.40 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vv.png" height="1" width="4" alt=\'Количество визитов: 0\' title=\'Количество визитов: 0\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="4" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="4" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="4" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td>&nbsp;</td><td><img align="bottom" src="/awstatsicons/other/vv.png" height="4" width="4" alt=\'Количество визитов: 0.22\' title=\'Количество визитов: 0.22\' /><img align="bottom" src="/awstatsicons/other/vp.png" height="3" width="4" alt=\'Страницы: 24.44\' title=\'Страницы: 24.44\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="5" width="4" alt=\'Хиты: 37.41\' title=\'Хиты: 37.41\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="4" width="4" alt=\'Объем: 288111.78\' title=\'Объем: 288111.78\' /></td>
</tr>
<tr valign="middle"><td>01<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">02<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">03<br /><span style="font-size: 9px;">Окт</span></td>
<td>04<br /><span style="font-size: 9px;">Окт</span></td>
<td>05<br /><span style="font-size: 9px;">Окт</span></td>
<td>06<br /><span style="font-size: 9px;">Окт</span></td>
<td>07<br /><span style="font-size: 9px;">Окт</span></td>
<td>08<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">09<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">10<br /><span style="font-size: 9px;">Окт</span></td>
<td>11<br /><span style="font-size: 9px;">Окт</span></td>
<td>12<br /><span style="font-size: 9px;">Окт</span></td>
<td>13<br /><span style="font-size: 9px;">Окт</span></td>
<td>14<br /><span style="font-size: 9px;">Окт</span></td>
<td>15<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">16<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">17<br /><span style="font-size: 9px;">Окт</span></td>
<td>18<br /><span style="font-size: 9px;">Окт</span></td>
<td>19<br /><span style="font-size: 9px;">Окт</span></td>
<td>20<br /><span style="font-size: 9px;">Окт</span></td>
<td>21<br /><span style="font-size: 9px;">Окт</span></td>
<td>22<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">23<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">24<br /><span style="font-size: 9px;">Окт</span></td>
<td>25<br /><span style="font-size: 9px;">Окт</span></td>
<td>26<br /><span style="font-size: 9px;">Окт</span></td>
<td>27<br /><span style="font-size: 9px;">Окт</span></td>
<td>28<br /><span style="font-size: 9px;">Окт</span></td>
<td>29<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">30<br /><span style="font-size: 9px;">Окт</span></td>
<td bgcolor="#EAEAEA">31<br /><span style="font-size: 9px;">Окт</span></td>
<td>&nbsp;</td><td valign="middle">Среднее</td>
</tr>
</table>
<br />
<table>
<tr><td width="80" bgcolor="#ECECEC">День</td><td width="80" bgcolor="#F4F090">Количество визитов</td><td width="80" bgcolor="#4477DD">Страницы</td><td width="80" bgcolor="#66DDEE">Хиты</td><td width="80" bgcolor="#2EA495">Объем</td></tr><tr><td>01 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>02 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>03 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>04 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>05 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>06 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>07 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>08 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>09 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>10 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>11 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>12 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>13 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>14 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>15 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>16 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>17 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>18 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>19 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>20 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>21 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>22 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>23 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>24 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>25 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>26 Окт 2021</td><td>5</td><td>567</td><td>835</td><td>6.56 МБ</td></tr>
<tr><td>27 Окт 2021</td><td>1</td><td>93</td><td>175</td><td>878.40 КБ</td></tr>
<tr><td>28 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>29 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>30 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>31 Окт 2021</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#ECECEC"><td>Среднее</td><td>0</td><td>24</td><td>37</td><td>281.36 КБ</td></tr>
<tr bgcolor="#ECECEC"><td>Всего</td><td>6</td><td>660</td><td>1,010</td><td>7.42 МБ</td></tr>
</table>
<br /></center>
</td></tr>
</table></td></tr></table><br />

<a name="daysofweek">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">День недели </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr><td align="center"><center>
<table>
<tr valign="bottom">
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="62" width="6" alt=\'Страницы: 141.75\' title=\'Страницы: 141.75\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="91" width="6" alt=\'Хиты: 208.75\' title=\'Хиты: 208.75\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="91" width="6" alt=\'Объем: 1.64 МБ\' title=\'Объем: 1.64 МБ\' /></td>
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="11" width="6" alt=\'Страницы: 23.25\' title=\'Страницы: 23.25\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="19" width="6" alt=\'Хиты: 43.75\' title=\'Хиты: 43.75\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="12" width="6" alt=\'Объем: 219.60 КБ\' title=\'Объем: 219.60 КБ\' /></td>
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td valign="bottom"><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
</tr>
<tr>
<td>Пнд</td><td>Втр</td><td>Срд</td><td>Чтв</td><td>Птн</td><td bgcolor="#EAEAEA">Сбт</td><td bgcolor="#EAEAEA">Вск</td></tr>
</table>
<br />
<table>
<tr><td width="80" bgcolor="#ECECEC">День</td><td width="80" bgcolor="#4477DD">Страницы</td><td width="80" bgcolor="#66DDEE">Хиты</td><td width="80" bgcolor="#2EA495">Объем</td></tr><tr><td>Пнд</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Втр</td><td>141</td><td>208</td><td>1.64 МБ</td></tr>
<tr><td>Срд</td><td>23</td><td>43</td><td>219.60 КБ</td></tr>
<tr><td>Чтв</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>Птн</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>Сбт</td><td>0</td><td>0</td><td>0</td></tr>
<tr bgcolor="#EAEAEA"><td>Вск</td><td>0</td><td>0</td><td>0</td></tr>
</table>
<br />
</center></td></tr>
</table></td></tr></table><br />

<a name="hours">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Часы </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr><td align="center">
<center>
<table>
<tr valign="bottom">
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="28" width="6" alt=\'Страницы: 93\' title=\'Страницы: 93\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="52" width="6" alt=\'Хиты: 175\' title=\'Хиты: 175\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="25" width="6" alt=\'Объем: 878.40 КБ\' title=\'Объем: 878.40 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="9" width="6" alt=\'Страницы: 28\' title=\'Страницы: 28\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="11" width="6" alt=\'Хиты: 34\' title=\'Хиты: 34\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="16" width="6" alt=\'Объем: 566.86 КБ\' title=\'Объем: 566.86 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="3" width="6" alt=\'Страницы: 10\' title=\'Страницы: 10\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="7" width="6" alt=\'Хиты: 22\' title=\'Хиты: 22\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="31" width="6" alt=\'Объем: 1.06 МБ\' title=\'Объем: 1.06 МБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="15" width="6" alt=\'Страницы: 50\' title=\'Страницы: 50\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="18" width="6" alt=\'Хиты: 59\' title=\'Хиты: 59\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="18" width="6" alt=\'Объем: 623.53 КБ\' title=\'Объем: 623.53 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="46" width="6" alt=\'Страницы: 155\' title=\'Страницы: 155\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="91" width="6" alt=\'Хиты: 305\' title=\'Хиты: 305\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="91" width="6" alt=\'Объем: 3.15 МБ\' title=\'Объем: 3.15 МБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="71" width="6" alt=\'Страницы: 239\' title=\'Страницы: 239\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="73" width="6" alt=\'Хиты: 247\' title=\'Хиты: 247\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="21" width="6" alt=\'Объем: 751.30 КБ\' title=\'Объем: 751.30 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="8" width="6" alt=\'Страницы: 25\' title=\'Страницы: 25\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="8" width="6" alt=\'Хиты: 26\' title=\'Хиты: 26\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="4" width="6" alt=\'Объем: 109.92 КБ\' title=\'Объем: 109.92 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="18" width="6" alt=\'Страницы: 60\' title=\'Страницы: 60\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="42" width="6" alt=\'Хиты: 142\' title=\'Хиты: 142\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="10" width="6" alt=\'Объем: 356.04 КБ\' title=\'Объем: 356.04 КБ\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
<td><img align="bottom" src="/awstatsicons/other/vp.png" height="1" width="6" alt=\'Страницы: 0\' title=\'Страницы: 0\' /><img align="bottom" src="/awstatsicons/other/vh.png" height="1" width="6" alt=\'Хиты: 0\' title=\'Хиты: 0\' /><img align="bottom" src="/awstatsicons/other/vk.png" height="1" width="6" alt=\'Объем: 0\' title=\'Объем: 0\' /></td>
</tr>
<tr><th width="19">0</th>
<th width="19">1</th>
<th width="19">2</th>
<th width="19">3</th>
<th width="19">4</th>
<th width="19">5</th>
<th width="19">6</th>
<th width="19">7</th>
<th width="19">8</th>
<th width="19">9</th>
<th width="19">10</th>
<th width="19">11</th>
<th width="19">12</th>
<th width="19">13</th>
<th width="19">14</th>
<th width="19">15</th>
<th width="19">16</th>
<th width="19">17</th>
<th width="19">18</th>
<th width="19">19</th>
<th width="19">20</th>
<th width="19">21</th>
<th width="19">22</th>
<th width="19">23</th>
</tr>
<tr>
<td><img src="/awstatsicons/clock/hr1.png" width="12" alt="0:00 - 1:00 am" /></td>
<td><img src="/awstatsicons/clock/hr2.png" width="12" alt="1:00 - 2:00 am" /></td>
<td><img src="/awstatsicons/clock/hr3.png" width="12" alt="2:00 - 3:00 am" /></td>
<td><img src="/awstatsicons/clock/hr4.png" width="12" alt="3:00 - 4:00 am" /></td>
<td><img src="/awstatsicons/clock/hr5.png" width="12" alt="4:00 - 5:00 am" /></td>
<td><img src="/awstatsicons/clock/hr6.png" width="12" alt="5:00 - 6:00 am" /></td>
<td><img src="/awstatsicons/clock/hr7.png" width="12" alt="6:00 - 7:00 am" /></td>
<td><img src="/awstatsicons/clock/hr8.png" width="12" alt="7:00 - 8:00 am" /></td>
<td><img src="/awstatsicons/clock/hr9.png" width="12" alt="8:00 - 9:00 am" /></td>
<td><img src="/awstatsicons/clock/hr10.png" width="12" alt="9:00 - 10:00 am" /></td>
<td><img src="/awstatsicons/clock/hr11.png" width="12" alt="10:00 - 11:00 am" /></td>
<td><img src="/awstatsicons/clock/hr12.png" width="12" alt="11:00 - 12:00 am" /></td>
<td><img src="/awstatsicons/clock/hr1.png" width="12" alt="0:00 - 1:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr2.png" width="12" alt="1:00 - 2:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr3.png" width="12" alt="2:00 - 3:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr4.png" width="12" alt="3:00 - 4:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr5.png" width="12" alt="4:00 - 5:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr6.png" width="12" alt="5:00 - 6:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr7.png" width="12" alt="6:00 - 7:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr8.png" width="12" alt="7:00 - 8:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr9.png" width="12" alt="8:00 - 9:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr10.png" width="12" alt="9:00 - 10:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr11.png" width="12" alt="10:00 - 11:00 pm" /></td>
<td><img src="/awstatsicons/clock/hr12.png" width="12" alt="11:00 - 12:00 pm" /></td>
</tr>
</table>
<br />
<table width="650"><tr>
<td align="center"><center>
<table>
<tr><td width="80" bgcolor="#ECECEC">Часы</td><td width="80" bgcolor="#4477DD">Страницы</td><td width="80" bgcolor="#66DDEE">Хиты</td><td width="80" bgcolor="#2EA495">Объем</td></tr><tr><td>00</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>01</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>02</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>03</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>04</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>05</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>06</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>07</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>08</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>09</td><td>93</td><td>175</td><td>878.40 КБ</td></tr>
<tr><td>10</td><td>28</td><td>34</td><td>566.86 КБ</td></tr>
<tr><td>11</td><td>0</td><td>0</td><td>0</td></tr>
</table>
</center></td><td width="10">&nbsp;</td><td align="center"><center>
<table>
<tr><td width="80" bgcolor="#ECECEC">Часы</td><td width="80" bgcolor="#4477DD">Страницы</td><td width="80" bgcolor="#66DDEE">Хиты</td><td width="80" bgcolor="#2EA495">Объем</td></tr>
<tr><td>12</td><td>10</td><td>22</td><td>1.06 МБ</td></tr>
<tr><td>13</td><td>50</td><td>59</td><td>623.53 КБ</td></tr>
<tr><td>14</td><td>155</td><td>305</td><td>3.15 МБ</td></tr>
<tr><td>15</td><td>239</td><td>247</td><td>751.30 КБ</td></tr>
<tr><td>16</td><td>25</td><td>26</td><td>109.92 КБ</td></tr>
<tr><td>17</td><td>60</td><td>142</td><td>356.04 КБ</td></tr>
<tr><td>18</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>19</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>20</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>21</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>22</td><td>0</td><td>0</td><td>0</td></tr>
<tr><td>23</td><td>0</td><td>0</td><td>0</td></tr>
</table>
</center></td></tr></table>
<br />
</center></td></tr>
</table></td></tr></table><br />


<a name="who">&nbsp;</a>

<a name="countries">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Посетители домены/страны (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.alldomains.html" target="awstatsbis">Полный список</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th width="32">&nbsp;</th><th colspan="2">Домены/Страны</th><th bgcolor="#4477DD" width="80">Страницы</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#2EA495" width="80">Объем</th><th>&nbsp;</th></tr>
<tr><td width="32"><img src="/awstatsicons/flags/ip.png" height="14" alt=\'Неизвестный\' title=\'Неизвестный\' /></td><td class="aws">Неизвестный</td><td>ip</td><td>660</td><td>1,010</td><td>7.42 МБ</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="170" height="5" alt=\'\' title=\'\' /><br />
<img src="/awstatsicons/other/hh.png" width="261" height="5" alt=\'\' title=\'\' /><br />
<img src="/awstatsicons/other/hk.png" width="261" height="5" alt=\'\' title=\'\' /></td></tr>
<tr><td width="32">&nbsp;</td><td colspan="2" class="aws"><span style="color: #666688">Остальные</span></td><td>0</td><td>0</td><td>0</td><td class="aws">&nbsp;</td></tr>
</table></td></tr></table><br />

<a name="visitors">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Хосты (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.allhosts.html" target="awstatsbis">Полный список</a> &nbsp; - &nbsp; <a href="awstats.vdi.lasthosts.html" target="awstatsbis">Последний визит</a> &nbsp; - &nbsp; <a href="awstats.vdi.unknownip.html" target="awstatsbis">Неразрешенный IP адрес</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>Хосты : 0 Известные, 2 Неизвестный<br />2 Уникальные посетители</th><th bgcolor="#4477DD" width="80">Страницы</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#2EA495" width="80">Объем</th><th width="120">Последний визит</th></tr>
<tr><td class="aws">192.168.14.211</td><td>646</td><td>952</td><td>5.68 МБ</td><td nowrap="nowrap">27 Окт 2021 - 09:43</td></tr>
<tr><td class="aws">127.0.0.1</td><td>14</td><td>58</td><td>1.74 МБ</td><td nowrap="nowrap">26 Окт 2021 - 14:34</td></tr>
</table></td></tr></table><br />

<a name="robots">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Роботы/Пауки посетители (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.allrobots.html" target="awstatsbis">Полный список</a> &nbsp; - &nbsp; <a href="awstats.vdi.lastrobots.html" target="awstatsbis">Последний визит</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>0 различные роботы*</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#2EA495" width="80">Объем</th><th width="120">Последний визит</th></tr>
</table></td></tr></table><span style="font: 11px verdana, arial, helvetica;">* Роботы отображенные здесь генерируют трафик не отображаемый посетителям, поэтому они не включены в остальную статистику.</span><br />
<br />


<a name="how">&nbsp;</a>

<a name="sessions">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Продолжительность визитов </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>Количество визитов: 6 - Среднее: 861 s</th><th bgcolor="#8888DD" width="80">Количество визитов</th><th bgcolor="#8888DD" width="80">Процент</th></tr>
<tr><td class="aws">0s-30s</td><td>2</td><td>33.3 %</td></tr>
<tr><td class="aws">30s-2mn</td><td>1</td><td>16.6 %</td></tr>
<tr><td class="aws">2mn-5mn</td><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><td class="aws">5mn-15mn</td><td>1</td><td>16.6 %</td></tr>
<tr><td class="aws">15mn-30mn</td><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><td class="aws">30mn-1h</td><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><td class="aws">1h+</td><td>1</td><td>16.6 %</td></tr>
<tr><td class="aws"><span style="color: #666688">Неизвестный</span></td><td>1</td><td>16.6 %</td></tr>
</table></td></tr></table><br />

<a name="filetypes">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Тип файла </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th colspan="3">Тип файла</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#66DDEE" width="80">Процент</th><th bgcolor="#2EA495" width="80">Объем</th><th bgcolor="#2EA495" width="80">Процент</th></tr>
<tr><td width="32"><img src="/awstatsicons/mime/pl.png" alt=\'\' title=\'\' /></td><td class="aws">pl</td><td class="aws">Dynamic Perl Script file</td><td>431</td><td>42.6 %</td><td nowrap="nowrap">3.72 МБ</td><td>50 %</td></tr>
<tr><td><img src="/awstatsicons/mime/image.png" alt=\'\' title=\'\' /></td><td class="aws">png</td><td class="aws">Image</td><td>315</td><td>31.1 %</td><td nowrap="nowrap">454.79 КБ</td><td>5.9 %</td></tr>
<tr><td><img src="/awstatsicons/mime/unknown.png" alt=\'\' title=\'\' /></td><td class="aws" colspan="2"><span style="color: #666688">Неизвестный</span></td><td>172</td><td>17 %</td><td nowrap="nowrap">199.14 КБ</td><td>2.6 %</td></tr>
<tr><td><img src="/awstatsicons/mime/php.png" alt=\'\' title=\'\' /></td><td class="aws">php</td><td class="aws">Dynamic PHP Script file</td><td>57</td><td>5.6 %</td><td nowrap="nowrap">106.16 КБ</td><td>1.3 %</td></tr>
<tr><td><img src="/awstatsicons/mime/jscript.png" alt=\'\' title=\'\' /></td><td class="aws">js</td><td class="aws">JavaScript file</td><td>21</td><td>2 %</td><td nowrap="nowrap">2.90 МБ</td><td>39 %</td></tr>
<tr><td><img src="/awstatsicons/mime/image.png" alt=\'\' title=\'\' /></td><td class="aws">gif</td><td class="aws">Image</td><td>8</td><td>0.7 %</td><td nowrap="nowrap">3.94 КБ</td><td>0 %</td></tr>
<tr><td><img src="/awstatsicons/mime/css.png" alt=\'\' title=\'\' /></td><td class="aws">css</td><td class="aws">Cascading Style Sheet file</td><td>6</td><td>0.5 %</td><td nowrap="nowrap">61.51 КБ</td><td>0.8 %</td></tr>
</table></td></tr></table><br />

<a name="downloads">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Downloads (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.downloads.html" target="awstatsbis">Полный список</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th colspan="2">Downloads: 0</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#66DDEE" width="80">206 Хиты</th><th bgcolor="#2EA495" width="80">Объем</th><th bgcolor="#2EA495" width="80">Средний размер</th></tr>
</table></td></tr></table><br />

<a name="urls">&nbsp;</a><a name="entry">&nbsp;</a><a name="exit">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Адрес страницы (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.urldetail.html" target="awstatsbis">Полный список</a> &nbsp; - &nbsp; <a href="awstats.vdi.urlentry.html" target="awstatsbis">Вхождение</a> &nbsp; - &nbsp; <a href="awstats.vdi.urlexit.html" target="awstatsbis">Выход</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>15 Различные url</th><th bgcolor="#4477DD" width="80">Просмотров</th><th bgcolor="#2EA495" width="80">Средний размер</th><th bgcolor="#CEC2E8" width="80">Вхождение</th><th bgcolor="#C1B2E2" width="80">Выход</th><th>&nbsp;</th></tr>
<tr><td class="aws"><a href="http://vdi/awstats/awstats.pl" target="url" rel="nofollow">/awstats/awstats.pl</a></td><td>428</td><td>8.87 КБ</td><td>4</td><td>3</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="261" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="261" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="3" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="2" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/events" target="url" rel="nofollow">/api/events</a></td><td>86</td><td>1.51 КБ</td><td>&nbsp;</td><td>1</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="53" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="45" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="2" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/pools" target="url" rel="nofollow">/api/pools</a></td><td>39</td><td>656 Байты</td><td>&nbsp;</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="24" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="19" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/controllers" target="url" rel="nofollow">/api/controllers</a></td><td>30</td><td>524 Байты</td><td>1</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="19" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="16" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="2" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/license/" target="url" rel="nofollow">/api/license/</a></td><td>16</td><td>646 Байты</td><td>&nbsp;</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="10" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="19" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/version/" target="url" rel="nofollow">/api/version/</a></td><td>15</td><td>470 Байты</td><td>&nbsp;</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="10" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="14" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/ws/subscriptions/" target="url" rel="nofollow">/api/ws/subscriptions/</a></td><td>15</td><td>4.55 КБ</td><td>&nbsp;</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="10" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="134" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/" target="url" rel="nofollow">/</a></td><td>11</td><td>1.90 КБ</td><td>1</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="7" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="56" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="2" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/resources" target="url" rel="nofollow">/api/resources</a></td><td>6</td><td>577 Байты</td><td>&nbsp;</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="4" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="17" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><a href="http://vdi/api/settings" target="url" rel="nofollow">/api/settings</a></td><td>3</td><td>527 Байты</td><td>&nbsp;</td><td>&nbsp;</td><td class="aws"><img src="/awstatsicons/other/hp.png" width="2" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hk.png" width="16" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/he.png" width="1" height="4" alt=\'\' title=\'\' /><br /><img src="/awstatsicons/other/hx.png" width="1" height="4" alt=\'\' title=\'\' /></td></tr>
<tr><td class="aws"><span style="color: #666688">Остальные</span></td><td>11</td><td>2.94 КБ</td><td>&nbsp;</td><td>1</td><td>&nbsp;</td></tr>
</table></td></tr></table><br />

<a name="os">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Операционные системы (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.osdetail.html" target="awstatsbis">Полный список/Версии</a> &nbsp; - &nbsp; <a href="awstats.vdi.unknownos.html" target="awstatsbis">Неизвестный</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th width="32">&nbsp;</th><th>Операционные системы</th><th bgcolor="#4477DD" width="80">Страницы</th><th bgcolor="#4477DD" width="80">Процент</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#66DDEE" width="80">Процент</th></tr>
<tr><td width="32"><img src="/awstatsicons/os/linux.png" alt=\'\' title=\'\' /></td><td class="aws"><b>Linux</b></td><td>651</td><td>98.6 %</td><td>894</td><td>88.5 %</td></tr>
<tr><td><img src="/awstatsicons/os/win.png" alt=\'\' title=\'\' /></td><td class="aws"><b>Windows</b></td><td>9</td><td>1.3 %</td><td>116</td><td>11.4 %</td></tr>
</table></td></tr></table><br />

<a name="browsers">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Браузеры (Топ 10) &nbsp; - &nbsp; <a href="awstats.vdi.browserdetail.html" target="awstatsbis">Полный список/Версии</a> &nbsp; - &nbsp; <a href="awstats.vdi.unknownbrowser.html" target="awstatsbis">Неизвестный</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th width="32">&nbsp;</th><th>Браузеры</th><th width="80">Грабер</th><th bgcolor="#4477DD" width="80">Страницы</th><th bgcolor="#4477DD" width="80">Процент</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#66DDEE" width="80">Процент</th></tr>
<tr><td width="32"><img src="/awstatsicons/browser/firefox.png" alt=\'\' title=\'\' /></td><td class="aws"><b>Firefox</b></td><td>Нет</td><td>651</td><td>98.6 %</td><td>894</td><td>88.5 %</td></tr>
<tr><td><img src="/awstatsicons/browser/chrome.png" alt=\'\' title=\'\' /></td><td class="aws"><b>Google Chrome</b></td><td>Нет</td><td>9</td><td>1.3 %</td><td>116</td><td>11.4 %</td></tr>
</table></td></tr></table><br />


<a name="refering">&nbsp;</a>

<a name="referer">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Соединение с сайтом из </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>Происхождение</th><th bgcolor="#4477DD" width="80">Страницы</th><th bgcolor="#4477DD" width="80">Процент</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#66DDEE" width="80">Процент</th></tr>
<tr><td class="aws"><b>Прямой адрес / Закладки</b></td><td>72</td><td>11 %</td><td>74</td><td>7.7 %</td></tr>
<tr><td class="aws"><b>Ссылки из поисковых систем</b> - <a href="awstats.vdi.refererse.html" target="awstatsbis">Полный список</a><br />
</td>
<td valign="top">&nbsp;</td><td valign="top">&nbsp;</td><td valign="top">&nbsp;</td><td valign="top">&nbsp;</td></tr>
<tr><td class="aws"><b>Ссылки из внешней страницы (остальные web сайты исключая поисковые системы)</b> - <a href="awstats.vdi.refererpages.html" target="awstatsbis">Полный список</a><br />
<table>
<tr><td class="aws">- <a href="https://192.168.5.248/awstats/awstats.pl" target="url" rel="nofollow">https://192.168.5.248/awstats/awstats.pl</a></td><td>376</td><td>648</td></tr>
<tr><td class="aws">- <a href="https://192.168.5.248" target="url" rel="nofollow">https://192.168.5.248</a></td><td>203</td><td>236</td></tr>
<tr><td class="aws">- <a href="https://192.168.5.248/cgi-bin/awstats.pl" target="url" rel="nofollow">https://192.168.5.248/cgi-bin/awstats.pl</a></td><td>0</td><td>1</td></tr>
</table></td>
<td valign="top">579</td><td valign="top">88.9 %</td><td valign="top">885</td><td valign="top">92.2 %</td></tr>
<tr><td class="aws"><b>Неизвестное происхождение</b></td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
</table></td></tr></table><br />


<a name="keys">&nbsp;</a>

<a name="keyphrases">&nbsp;</a><a name="keywords">&nbsp;</a><br />
<table width="100%" cellpadding="0" cellspacing="0"><tr><td width="50%" valign="top">
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="95%">Поисковые&nbsp;Ключевые фразы (Топ 10)<br /><a href="awstats.vdi.keyphrases.html" target="awstatsbis">Полный список</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>0 Различные ключевые фразы</th><th bgcolor="#8888DD" width="80">Поиск</th><th bgcolor="#8888DD" width="80">Процент</th></tr>
</table></td></tr></table><br />

</td>
<td> &nbsp; </td><td width="50%" valign="top">
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="95%">Поисковые&nbsp;Ключевые слова (Топ 10)<br /><a href="awstats.vdi.keywords.html" target="awstatsbis">Полный список</a> </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>0 различные ключевые слова</th><th bgcolor="#8888DD" width="80">Поиск</th><th bgcolor="#8888DD" width="80">Процент</th></tr>
</table></td></tr></table><br />

</td>
</tr></table>

<a name="other">&nbsp;</a>

<a name="misc">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Смешанные </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th>Смешанные</th><th width="100">&nbsp;</th><th width="100">&nbsp;</th></tr>
<tr><td class="aws">Добавить в закладки (предполагаемый)</td><td>9 / 2 Посетители</td><td>450 %</td></tr>
</table></td></tr></table><br />

<a name="errors">&nbsp;</a><br />
<table class="aws_border sortable" border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td class="aws_title" width="70%">Статусы ошибок HTTP </td><td class="aws_blank">&nbsp;</td></tr>
<tr><td colspan="2">
<table class="aws_data" border="1" cellpadding="2" cellspacing="0" width="100%">
<tr bgcolor="#ECECEC"><th colspan="2">Статусы ошибок HTTP*</th><th bgcolor="#66DDEE" width="80">Хиты</th><th bgcolor="#66DDEE" width="80">Процент</th><th bgcolor="#2EA495" width="80">Объем</th></tr>
<tr><td><a href="awstats.vdi.errors404.html" target="awstatsbis">404</a></td><td class="aws">Document Not Found (hits on favicon excluded)</td><td>2</td><td>100 %</td><td>1.44 КБ</td></tr>
</table></td></tr></table><span style="font: 11px verdana, arial, helvetica;">* Коды отображенные здесь генерируют трафик не отображаемый посетителям, поэтому они не включены в остальную статистику.</span><br />
<br />

<br /><br />
<span dir="ltr" style="font: 11px verdana, arial, helvetica; color: #000000;"><b>Advanced Web Statistics 7.5 (build 20160301)</b> - <a href="http://www.awstats.org" target="awstatshome">Создано awstats</a></span><br />

<br />
</body>
</html>
'''
}
