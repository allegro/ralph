using System;

namespace DonPedro.DTO
{
	public class DiskShareMountDTOResponse : BaseDTOResponse
	{
		public string Volume { get; set; }
		public string SerialNumber { get; set; }
		public string Size { get; set; }
	}
}
