using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class StorageDTOResponse : BaseDTOResponse
	{
		public string sn { get; set; }
		public string mountPoint { get; set; }
		public string size { get; set; }
	}
}
