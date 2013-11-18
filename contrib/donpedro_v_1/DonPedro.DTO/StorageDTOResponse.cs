using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class StorageDTOResponse : BaseDTOResponse
	{
		public string Sn { get; set; }
		public string MountPoint { get; set; }
		public string Size { get; set; }
	}
}
