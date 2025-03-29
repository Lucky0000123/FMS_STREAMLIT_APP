import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
from pathlib import Path

class FMSStreamlitService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FMSStreamlitService"
    _svc_display_name_ = "FMS Streamlit Dashboard Service"
    _svc_description_ = "Runs the FMS Streamlit Dashboard as a Windows Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PID_INFO,
                ('Starting the %s service' % self._svc_name_)
            )
            
            # Get the path to run_service.py
            service_path = Path(__file__).parent / "run_service.py"
            
            # Run the Streamlit app
            while self.running:
                try:
                    import run_service
                    run_service.run_streamlit()
                except Exception as e:
                    servicemanager.LogErrorMsg(f"Error running Streamlit: {str(e)}")
                    time.sleep(5)  # Wait before retrying
                    
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {str(e)}")
            self.running = False

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FMSStreamlitService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FMSStreamlitService) 