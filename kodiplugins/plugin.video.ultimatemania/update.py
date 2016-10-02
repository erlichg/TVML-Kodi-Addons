import xbmc,xbmcgui,shutil
import os




def reset():
    print '############################################################       DELETING SETTINGS             ###############################################################'
    xbmc_cache_path = os.path.join(xbmc.translatePath('special://home/userdata/addon_data'), 'plugin.video.ultimatemania')
    if os.path.exists(xbmc_cache_path)==True:    
        for root, dirs, files in os.walk(xbmc_cache_path):
            file_count = 0
            file_count += len(files)
        
        
            if file_count > 0:
    

                
                for f in files:
                    try:
                        if not 'paki' in f:
                            os.unlink(os.path.join(root, f))
                    except:
                        pass
                for d in dirs:
                    try:
                        shutil.rmtree(os.path.join(root, d))
                    except:
                        pass
                dialog = xbmcgui.Dialog()
                dialog.ok("UltimateMania", "", "All Reset Try Again")
                    
            else:
                pass

            
   
    cookie_path = os.path.join(xbmc_cache_path, 'cookies')        
    if os.path.exists(cookie_path) == False:
            os.makedirs(cookie_path)            


if __name__ == '__main__': 
        reset() #silent
if __name__ == 'update':
        reset() #silent
