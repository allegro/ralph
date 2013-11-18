using System;

namespace DonPedro.DTO
{
	public class DeviceDTOResponse : BaseDTOResponse
	{
		public string Sn { get; set; }
		public string Caption { get; set; }
		public string Version { get; set; }
		public string Vendor { get; set; }
	}
}
