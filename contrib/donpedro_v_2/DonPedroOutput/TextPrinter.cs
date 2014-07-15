using System;
using DonPedro.Detectors;
using DonPedro.DTO;

namespace DonPedroOutput
{
	public class TextPrinter
	{
		public void Print(Detector d, bool jsonOnly)
		{
			if (jsonOnly)
			{
				Console.WriteLine(d.GetAllComponentsJSON());
			}
			else
			{
				Console.WriteLine("Detected CPUs:");
				foreach(ProcessorDTOResponse item in d.GetProcessorsInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected memory:");
				foreach(MemoryDTOResponse item in d.GetMemoryInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected OS:");
				OperatingSystemDTOResponse os = d.GetOperatingSystemInfo();
				PropertiesPrinter.Print(os);
				
				Console.WriteLine("\nDetected storage:");
				foreach(StorageDTOResponse item in d.GetStorageInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected IP addresses:");
				foreach(IPAddressDTOResponse item in d.GetIPAddressInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected MAC addresses:");
				foreach(MacAddressDTOResponse item in d.GetMacAddressInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected fc cards:");
				foreach(FibreChannelDTOResponse item in d.GetFibreChannelInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected shares:");
				foreach(DiskShareMountDTOResponse item in d.GetDiskShareMountInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected software:");
				foreach(SoftwareDTOResponse item in d.GetSoftwareInfo())
				{
					PropertiesPrinter.Print(item);
				}
				
				Console.WriteLine("\nDetected device:");
				DeviceDTOResponse dev = d.GetDeviceInfo();
				PropertiesPrinter.Print(dev);
			}
		}
	}
}
