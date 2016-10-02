import os,xbmc


addon_path = xbmc.translatePath(os.path.join('special://home/addons', 'repository.xunitytalk'))
addonxml=xbmc.translatePath(os.path.join('special://home/addons', 'repository.xunitytalk','addon.xml'))



WRITEME='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <addon id="repository.xunitytalk" name=".[COLOR blue]X[/COLOR]unity[COLOR blue]T[/COLOR]alk Repository" version="1.1.1" provider-name=".[COLOR blue]X[/COLOR]unity[COLOR blue]T[/COLOR]alk">
                <extension point="xbmc.addon.repository" name="Mikey1234 Addon Repository">
                        <info compressed="false">http://xtyrepo.me/xunitytalk/addons/addons.xml</info>
                        <checksum>http://xtyrepo.me/xunitytalk/addons/addons.xml.md5</checksum>
                        <datadir zip="true">http://xtyrepo.me/xunitytalk/addons</datadir>
                </extension>
                <extension point="xbmc.addon.metadata">
                        <summary>The Best Third Party Addons for XBMC, .[COLOR blue]X[/COLOR]unity[COLOR blue]T[/COLOR]alk</summary>
                        <description>The Best Third Party Addons for XBMC, .[COLOR blue]X[/COLOR]unity[COLOR blue]T[/COLOR]alk</description>
                        <platform>all</platform>
                </extension>
        </addon>'''




       

if os.path.exists(addon_path) == False:
    os.makedirs(addon_path)    
    if os.path.exists(addonxml) == False:

        f = open(addonxml, mode='w')
        f.write(WRITEME)
        f.close()

        xbmc.executebuiltin('UpdateLocalAddons') 
        xbmc.executebuiltin("UpdateAddonRepos")




addon_path = xbmc.translatePath(os.path.join('special://home/addons', 'script.icechannel.extn.xunitytalk'))
addonxml=xbmc.translatePath(os.path.join('special://home/addons', 'script.icechannel.extn.xunitytalk','addon.xml'))

WRITEME='''<?xml version="1.0" encoding="UTF-8"?>
        <addon id="script.icechannel.extn.xunitytalk" version="0.0.1" name=".[COLOR blue]X[/COLOR]unity Talk iStream Extensions" provider-name="[COLOR blue]X[/COLOR]unity[COLOR blue]T[/COLOR]alk">
            <requires>
                <import addon="xbmc.python" version="2.1.0"/>
            </requires>
                <extension library="default.py" point="xbmc.service" />
                        <summary lang="en">iStream Extensions by xunitytalk.com</summary>
            <extension point="xbmc.python.module" library="lib" />
            <extension point="xbmc.addon.metadata">
                        <description lang="en">iStream Extensions by Xunity Talk Movies Tv Shows Kids Live</description>
                        <!--<provides>video</provides>-->
                        <platform></platform>
                        <language></language>
                        <license></license>
                        <forum></forum>
                        <website></website>
                        <source></source>
                        <email></email>
            </extension>
          <extension point="xbmc.service" library="service.py" start="login" />
        </addon>'''




if os.path.exists(addon_path) == False:
    os.makedirs(addon_path)    
    if os.path.exists(addonxml) == False:

        f = open(addonxml, mode='w')
        f.write(WRITEME)
        f.close()

        xbmc.executebuiltin('UpdateLocalAddons') 
        xbmc.executebuiltin("UpdateAddonRepos")


