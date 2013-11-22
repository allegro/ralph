using System;
using DonPedro.DTO;
using DonPedro.Detectors;
using System.Collections.Generic;
using System.Management;

namespace DonPedro.Detectors
{
	public class Detector
	{
		WMIDetectorSource wmiDetector;
		
		public Detector()
		{
			wmiDetector = new WMIDetectorSource();
		}
		
		public List<ProcessorDTOResponse> GetProcessorsInfo()
		{
			return  wmiDetector.GetProcessorsInfo();
		}
		
		public List<MemoryDTOResponse> GetMemoryInfo()
		{
			return wmiDetector.GetMemoryInfo();
		}
		
		public OperatingSystemDTOResponse GetOperatingSystemInfo()
		{
			return wmiDetector.GetOperatingSystemInfo();
		}
		
		public List<StorageDTOResponse> GetStorageInfo()
		{
			return wmiDetector.GetStorageInfo();
		}
		
		public List<SoftwareDTOResponse> GetSoftwareInfo()
		{
			WindowsRegistryDetectorSource regInfo = new WindowsRegistryDetectorSource();
			List<SoftwareDTOResponse> software = regInfo.GetSoftwareInfo();
			if (software.Count == 0) {

				software = wmiDetector.GetSoftwareInfo();
			}
			return software;
		}
		
		public List<IPAddressDTOResponse> GetIPAddressInfo()
		{
			return wmiDetector.GetIPAddressInfo();
		}
		
		public List<MacAddressDTOResponse> GetMacAddressInfo()
		{
			return wmiDetector.GetMacAddressInfo();
		}
		
		public List<FibreChannelDTOResponse> GetFibreChannelInfo()
		{
			FCInfoDetectorSource fcinfo = new FCInfoDetectorSource();
			List<FibreChannelDTOResponse> fc = fcinfo.GetFibreChannelInfo();
			if (fc.Count == 0) {
				fc = wmiDetector.GetFibreChannelInfo();
			}
			return fc;
		}
		
		public List<DiskShareMountDTOResponse> GetDiskShareMountInfo()
		{
			return wmiDetector.GetDiskShareMountInfo();
		}
		
		public DeviceDTOResponse GetDeviceInfo()
		{
			return wmiDetector.GetDeviceInfo();
		}
		
		public string GetAllComponentsJSON()
		{
			string json = "{\"data\":{";
			json += "\"status\":\"success\",";
			json += "\"date\":\"" + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "\",";
			json += "\"plugin\":\"donpedro\",";
			json += "\"messages\":[],";
			json += "\"device\":{";
			DeviceDTOResponse deviceInfo = GetDeviceInfo();
			json += "\"model_name\":\"" + deviceInfo.ModelName + "\",";
			json += "\"serial_number\":\"" + deviceInfo.SerialNumber + "\",";
			json += "\"system_ip_addresses\":[" + string.Join(",", GetIPAddressInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"mac_addresses\":[" + string.Join(",", GetMacAddressInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"disks\":[" + string.Join(",", GetStorageInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"fibrechannel_cards\":[" + string.Join(",", GetFibreChannelInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"disk_shares\":[" + string.Join(",", GetDiskShareMountInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"memory\":[" + string.Join(",", GetMemoryInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"processors\":[" + string.Join(",", GetProcessorsInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			json += "\"installed_software\":[" + string.Join(",", GetSoftwareInfo().ConvertAll(s => s.ToJSON()).ToArray()) + "],";
			OperatingSystemDTOResponse operatingSystem = GetOperatingSystemInfo();
			json += "\"system_memory\":\"" + operatingSystem.SystemMemory + "\",";
			json += "\"system_storage\":\"" + operatingSystem.SystemStorage + "\",";
			json += "\"system_cores_count\":\"" + operatingSystem.SystemCoresCount + "\"";
			json += "},";
			json += "\"results_priority\":{";
			json += "\"model_name\":25,";
			json += "\"serial_number\":20,";
			json += "\"system_ip_addresses\":60,";
			json += "\"mac_addresses\":50,";
			json += "\"disks\":30,";
			json += "\"fibrechannel_cards\":60,";
			json += "\"disk_shares\":30,";
			json += "\"memory\":60,";
			json += "\"processors\":60,";
			json += "\"installed_software\":60,";
			json += "\"system_memory\":60,";
			json += "\"system_storage\":30,";
			json += "\"system_cores_count\":60";
			return json + "}}}";
		}
	}
}
