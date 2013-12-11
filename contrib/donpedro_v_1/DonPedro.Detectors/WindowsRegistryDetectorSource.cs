using System;
using System.Collections.Generic;
using System.Diagnostics;
using DonPedro.DTO;
using DonPedro.Utils;
using Microsoft.Win32;

namespace DonPedro.Detectors
{
	public class WindowsRegistryDetectorSource
	{
		public List<SoftwareDTOResponse> GetSoftwareInfo()
		{
			List<SoftwareDTOResponse> software = new List<SoftwareDTOResponse>();

			software.AddRange(GetSoftwareFromLocalMachine32());
			software = MergeSoftwareLists(software, GetSoftwareFromLocalMachine64());
			
			return software;
		}
		
		protected List<SoftwareDTOResponse> MergeSoftwareLists(List<SoftwareDTOResponse> baseList, List<SoftwareDTOResponse> newList)
		{
			List<SoftwareDTOResponse> software = new List<SoftwareDTOResponse>();
			
			software.AddRange(baseList);
			
			foreach (SoftwareDTOResponse application in newList)
			{
				SoftwareDTOResponse result = software.Find(
					delegate (SoftwareDTOResponse item) {
						return item.Label == application.Label && item.Version == application.Version;
					}
				);
				if (result != null) {
					continue;
				}
				software.Add(application);
			}

			return software;
		}
		
		protected List<SoftwareDTOResponse> GetSoftwareFromCurrentUser()
		{
			string path = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";
			return GetItemsFromRegistry(Registry.CurrentUser, path);
		}
		
		protected List<SoftwareDTOResponse> GetSoftwareFromLocalMachine32()
		{
			string path = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";
			return GetItemsFromRegistry(Registry.LocalMachine, path);
		}
		
		protected List<SoftwareDTOResponse> GetSoftwareFromLocalMachine64()
		{
			string path = @"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall";
			return GetItemsFromRegistry(Registry.LocalMachine, path);
		}
		
		protected List<SoftwareDTOResponse> GetItemsFromRegistry(RegistryKey key, string path)
		{
			List<SoftwareDTOResponse> software = new List<SoftwareDTOResponse>();
			
			using (RegistryKey rk = key.OpenSubKey(path))
			{
				foreach (string skName in rk.GetSubKeyNames())
				{
					using (RegistryKey sk = rk.OpenSubKey(skName))
					{
						try
						{
							SoftwareDTOResponse application = new SoftwareDTOResponse();
							application.Label = sk.GetValue("DisplayName").ToString();
							application.Vendor = sk.GetValue("Publisher").ToString();
							application.Version = sk.GetValue("DisplayVersion").ToString();
							
							software.Add(application);
						}
						catch (Exception)
						{
						}
					}
				}
			}
			return software;
		}
	}
}
