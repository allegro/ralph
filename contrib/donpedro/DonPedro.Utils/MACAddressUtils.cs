using System;

namespace DonPedro.Utils
{
	public class MACAddressUtils
	{
		public static string NormalizeMACAddress(string mac)
		{
			mac = mac.Replace(":", "");
			mac = mac.Replace("-", "");
			
			return mac;
		}
	}
}
