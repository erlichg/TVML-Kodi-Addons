from collections import OrderedDict
import multiprocessing

PROCESSES = OrderedDict()

SERVICES = OrderedDict()

manager = multiprocessing.Manager()

CONTEXT = manager.dict()

REPOSITORIES = [
        #{'name': 'Kodi repository', 'dirs': [{'xml': 'http://mirrors.kodi.tv/addons/krypton/addons.xml',
        #                                      'download': 'http://mirrors.kodi.tv/addons/krypton'}]},
        {'name': 'Kodi Israel', 'dirs': [{'xml': 'https://raw.githubusercontent.com/kodil/kodil/master/addons.xml',
                                          'download': 'https://raw.githubusercontent.com/kodil/kodil/master/repo'}]},
        #{'name': 'Exodus repository',
        # 'dirs': [{'xml': 'https://offshoregit.com/exodus/addons.xml', 'download': 'https://offshoregit.com/exodus/'}]}
]