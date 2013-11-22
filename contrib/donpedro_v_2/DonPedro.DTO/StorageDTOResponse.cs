using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class StorageDTOResponse : BaseDTOResponse
	{
		public string Label { get; set; }
		public string SerialNumber { get; set; }
		public string MountPoint { get; set; }
		public string Size { get; set; }
	}
}
