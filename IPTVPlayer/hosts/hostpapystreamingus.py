# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import copy
import re
import urllib
import base64
try:    import json
except Exception: import simplejson as json
from datetime import datetime
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, unpackJS, VIDEOMEGA_decryptPlayerParams
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://papystreaming.us/'

class PapyStreamingUS(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'PapyStreamingUS', 'cookie':'PapyStreamingUS.cookie'})
        
        self.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/44.0 (Chrome)"
        self.HEADER     = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL    = 'http://papystreaming.us/'
        self.SRCH_URL    = self.getFullUrl('?s=')
        self.DEFAULT_ICON_URL = 'http://i0.wp.com/papystreaming.us/wp-content/uploads/2016/10/logos.png'
        
        self.MAIN_CAT_TAB = [{'category':'categories',     'title': _('Categories'),     'url':self.MAIN_URL },
                             {'category':'search',         'title': _('Search'),         'search_item':True  },
                             {'category':'search_history', 'title': _('Search history'),                     }]
        
    def listCategories(self, cItem, category):
        printDBG("PapyStreamingUS.listCategories")
        
        params = dict(cItem)
        params.update({'category':category, 'title':_('All')})
        self.addDir(params)
            
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="sub-menu"', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>');
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            params = dict(cItem)
            params.update({'category':category, 'title':self.cleanHtmlStr(item), 'url':self.getFullUrl(url)})
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("PapyStreamingUS.listItems")
        
        tmp = cItem['url'].split('?')
        url = tmp[0]
        if len(tmp) > 1:
            arg = tmp[1]
        else: arg = ''
        
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%s' % page
        if '' != arg:
            url += '?' + arg
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, '/page/(%s)[^0-9]' % (page+1))[0]
        if nextPage != '':
            nextPage = True
        else:
            nextPage = False

        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="post"', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>');
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', ignoreCase=True)[0]
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>', caseSensitive=False)[1] )
            if title == '': title = url.split('/')[-1].replace('-', ' ').title()
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', ignoreCase=True)[0]
            params = {'title':title, 'url':self.getFullUrl(url), 'icon':self.getFullUrl(icon), 'desc':self.cleanHtmlStr( item )}
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("PapyStreamingUS.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []

        playerUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?)"')[0]
        
        if self.up.getDomain(cItem['url']) == self.up.getDomain(playerUrl):
            AJAX_HEADER = dict(self.AJAX_HEADER)
            AJAX_HEADER['Referer'] = cItem['url']
            params = dict(self.defaultParams)
            params['header'] = AJAX_HEADER
            sts, data = self.cm.getPage(playerUrl, params)
            if not sts: return []
            url = self.getFullUrl('/e/Htplugins/Loader.php')
            params['header']['Referer'] = playerUrl
            data = self.cm.ph.getDataBeetwenMarkers(data, 'oad(', ')', False)[1]
            data = self.cm.ph.getSearchGroups(data, '"([^"]+?)"')[0]
            sts, data = self.cm.getPage(url, params, {'data':data})
            if not sts: return []
            
            try:
                data = byteify(json.loads(data))
                for idx in range(len(data)):
                    urlTab.append({'name':data['q'][idx], 'url':data['l'][idx]})
            except Exception:
                printExc()
        else:
            urlTab = self.up.getVideoLinkExt(playerUrl)
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'items')
    #ITEMS
        elif category == 'items':
            self.listItems(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, PapyStreamingUS(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
