using System;

namespace DonPedro.Utils
{
	public class Blacklists
	{
		private static string[] macPreficBlacklist = {
			"505054", "33506F", "009876", "000000", "00000C", "204153",
			"149120", "020054", "FEFFFF", "1AF920", "020820", "DEAD2C",
			"FEAD4D"
		};
		private static string[] diskVendorBlacklist = {
			"lsi", "lsilogic", "vmware", "3pardata"
		};
		private static string[] diskProductBlacklist = {
			"mr9261-8i", "9750-4i", "msa2324fc", "logical volume",
			"virtualdisk", "virtual-disk", "multi-flex", "1815      fastt",
			"comstar"
		};
		
		public static string[] MacPrefixBlacklist
		{
			get
			{
				return macPreficBlacklist;
			}
		}
		
		public static string[] DiskVendorBlacklist
		{
			get
			{
				return diskVendorBlacklist;
			}
		}
		
		public static string[] DiskProductBlacklist
		{
			get
			{
				return diskProductBlacklist;
			}
		}
	}
}
