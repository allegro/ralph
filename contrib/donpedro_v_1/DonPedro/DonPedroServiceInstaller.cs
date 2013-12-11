using System;
using System.ComponentModel;
using System.ServiceProcess;
using System.Configuration.Install;

namespace DonPedro
{
	[RunInstaller(true)]
	public class DonPedroServiceInstaller : Installer
	{
		private ServiceProcessInstaller processInstaller;
		private ServiceInstaller serviceInstaller;
		
		public DonPedroServiceInstaller()
		{
			processInstaller = new ServiceProcessInstaller();
			serviceInstaller = new ServiceInstaller();
			
			processInstaller.Account = ServiceAccount.LocalSystem;
			processInstaller.Username = null;
			processInstaller.Password = null;
			
			serviceInstaller.StartType = ServiceStartMode.Automatic;
			serviceInstaller.ServiceName = "DonPedro";
			serviceInstaller.DisplayName = "DonPedro agent";
			
			Installers.Add(serviceInstaller);
			Installers.Add(processInstaller);
		}
	}
}
