import threading
import os
from .compatibility import version_info

class Connector:
    """Own all COM proxies on the initializing STA thread. Never pass proxies out."""
    def __init__(self, start=False, expected_year=None, allow_future=None):
        import pythoncom
        import win32com.client
        import win32event,win32api
        self.event=win32event; self.api=win32api
        self.mutex=win32event.CreateMutex(None,False,'Local\\AI_CAD_BRIDGE_INVENTOR')
        if win32event.WaitForSingleObject(self.mutex,0) not in (win32event.WAIT_OBJECT_0,win32event.WAIT_ABANDONED):
            win32api.CloseHandle(self.mutex)
            raise RuntimeError('Another AI CAD Bridge process is using Inventor')
        self.owner=threading.get_ident()
        self.com=pythoncom
        initialized=False
        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            initialized=True
            try: raw=pythoncom.GetActiveObject('Inventor.Application').QueryInterface(pythoncom.IID_IDispatch)
            except pythoncom.com_error:
                if not start: raise RuntimeError('Inventor is not available in the Running Object Table; use --start')
                raw=pythoncom.CoCreateInstance('Inventor.Application',None,pythoncom.CLSCTX_LOCAL_SERVER,pythoncom.IID_IDispatch)
            # Bind the Application interface explicitly: the Inventor coclass has no
            # default_interface in some makepy versions (GetActiveObject then fails).
            info = raw.GetTypeInfo()
            typelib, _ = info.GetContainingTypeLib()
            guid, lcid, _, major, minor, _ = typelib.GetLibAttr()
            module = win32com.client.gencache.EnsureModule(guid, lcid, major, minor)
            interface_id = info.GetTypeAttr()[0]
            cls=win32com.client.gencache.GetClassForCLSID(interface_id)
            self.app=cls(raw)
            if start: self.app.Visible=True
            self.c=module.constants
            if expected_year is None and os.getenv('AI_CAD_INVENTOR_YEAR'):
                expected_year = int(os.environ['AI_CAD_INVENTOR_YEAR'])
            if allow_future is None: allow_future = os.getenv('AI_CAD_ALLOW_FUTURE') == '1'
            self.version = version_info(self.app.SoftwareVersion.Major,
                                        self.app.SoftwareVersion.DisplayVersion,
                                        expected_year, allow_future)
        except BaseException:
            if initialized: pythoncom.CoUninitialize()
            self.event.ReleaseMutex(self.mutex);self.api.CloseHandle(self.mutex)
            raise
    def check_thread(self):
        if threading.get_ident()!=self.owner: raise RuntimeError('COM access outside owner STA')
    def close(self):
        self.check_thread()
        self.app=None
        self.com.CoUninitialize()
        self.event.ReleaseMutex(self.mutex);self.api.CloseHandle(self.mutex)
    def status(self):
        self.check_thread()
        return {'version':self.version,'documents':self.app.Documents.Count,'ready':bool(self.app.Ready),'sta_thread':self.owner}
    def collection(self, objects):
        self.check_thread()
        result=self.app.TransientObjects.CreateObjectCollection()
        for item in objects: result.Add(item)
        return result
