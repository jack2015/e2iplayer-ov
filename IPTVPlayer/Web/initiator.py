#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
from Plugins.Extensions.OpenWebif.WebChilds.Toplevel import addExternalChild
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from webSite import StartPage, redirectionPage, hostsPage, useHostPage, downloaderPage, settingsPage, logsPage, searchPage
from twisted.web import static

from Plugins.Extensions.IPTVPlayer.tools.iptvtools import GetPluginDir
import settings

IPTVwebRoot = static.File(GetPluginDir('Web/')) #webRoot = pluginDir to get access to icons and logos
IPTVwebRoot.putChild("icons", static.File(GetPluginDir('icons/')))
IPTVwebRoot.putChild("", StartPage())
IPTVwebRoot.putChild("hosts", hostsPage())
IPTVwebRoot.putChild("usehost", useHostPage())
IPTVwebRoot.putChild("downloader", downloaderPage())
IPTVwebRoot.putChild("settings", settingsPage())
IPTVwebRoot.putChild("logs", logsPage())
IPTVwebRoot.putChild("search", searchPage())


def checkForFC():
	ret = False
	if os.path.exists(resolveFilename(SCOPE_PLUGINS, 'Extensions/OpenWebif/controllers/base.pyo')):
		myfileName = resolveFilename(SCOPE_PLUGINS, 'Extensions/OpenWebif/controllers/base.pyo')
	else:
		return False

	try:
		with open(myfileName, "r") as myfile:
			data = myfile.read()
			myfile.close()
		if data.find('fancontrol') > 0 and data.find('iptvplayer') < 0:
			ret = True
			data = None
	except Exception:
		pass

	data = None
	return ret


# registration for openwebif
if checkForFC() == True and not os.path.exists(resolveFilename(SCOPE_PLUGINS, 'Extensions/FanControl2/FC2webSite.pyo')):
	fcRoot = static.File(GetPluginDir('Web/'))
	fcRoot.putChild("", redirectionPage())
	try:
		addExternalChild(("fancontrol", fcRoot, "E2iPlayer", settings.WebInterfaceVersion))
		addExternalChild(("iptvplayer", IPTVwebRoot, None, None))
	except Exception:
		print("[E2iPlayer] exception registering Web interface in FC mode")
else: #user still can use IPTV web interface, but would need to mark URL manually depending on the openWebIf version
	try:
		addExternalChild(("iptvplayer", IPTVwebRoot, "E2iPlayer", settings.WebInterfaceVersion))
		addExternalChild(("e2iplayer", IPTVwebRoot, "E2iPlayer", settings.WebInterfaceVersion))
	except Exception:
		print("[E2iPlayer] exception registering Web interface in NATIVE mode")
