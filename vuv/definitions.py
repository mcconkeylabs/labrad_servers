import os



ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


manager_parts = ['scalabrad-0.8.3', 'bin', 'labrad.bat']
web_parts = ['scalabrad-web-server-2.0.4', 'bin', 'labrad-web.bat']

def gen_root_path(parts):
    p = [ROOT_DIR, '..'] + parts
    return os.path.abspath(os.path.join(p))

MANAGER_SCRIPT = gen_root_path(manager_parts)
WEB_SCRIPT = gen_root_path(web_parts)