using System;
using DonPedro.Detectors;
using DonPedro.DTO;

namespace DonPedroOutput
{
	class Program
	{
		public static void Main(string[] args)
		{
			Detector d = new Detector();
			
			Console.WriteLine("Detected CPUs:");
			foreach(ProcessorDTOResponse item in d.GetProcessorsInfo())
			{
				foreach(var prop in item.GetType().GetProperties()) {
					Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(item, null));
				}
				Console.WriteLine();
			}
			
			Console.WriteLine("\nDetected memory:");
			foreach(MemoryDTOResponse item in d.GetMemoryInfo())
			{
				foreach(var prop in item.GetType().GetProperties()) {
					Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(item, null));
				}
				Console.WriteLine();
			}
			
			Console.WriteLine("\nDetected OS:");
			OperatingSystemDTOResponse os = d.GetOperatingSystemInfo();
			foreach(var prop in os.GetType().GetProperties()) {
				Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(os, null));
			}
			Console.WriteLine();
			
			Console.WriteLine("\nDetected storage:");
			foreach(StorageDTOResponse item in d.GetStorageInfo())
			{
				foreach(var prop in item.GetType().GetProperties()) {
					Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(item, null));
				}
				Console.WriteLine();
			}
			
			Console.WriteLine("\nDetected ethernets:");
			foreach(EthernetDTOResponse item in d.GetEthernetInfo())
			{
				foreach(var prop in item.GetType().GetProperties()) {
					Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(item, null));
				}
				Console.WriteLine();
			}
			
			Console.WriteLine("\nDetected fc cards:");
			foreach(FibreChannelDTOResponse item in d.GetFibreChannelInfo())
			{
				foreach(var prop in item.GetType().GetProperties()) {
					Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(item, null));
				}
				Console.WriteLine();
			}
			
			Console.WriteLine("\nDetected shares:");
			foreach(DiskShareMountDTOResponse item in d.GetDiskShareMountInfo())
			{
				foreach(var prop in item.GetType().GetProperties()) {
					Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(item, null));
				}
				Console.WriteLine();
			}
			
			Console.WriteLine("\nDetected device:");
			DeviceDTOResponse dev = d.GetDeviceInfo();
			foreach(var prop in dev.GetType().GetProperties()) {
				Console.WriteLine("\t{0}: {1}", prop.Name, prop.GetValue(dev, null));
			}
			Console.WriteLine();

			Console.Write("Press any key to continue . . . ");
			Console.ReadKey(true);
		}
	}
}