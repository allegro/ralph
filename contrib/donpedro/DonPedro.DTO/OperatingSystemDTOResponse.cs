using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class OperatingSystemDTOResponse : BaseDTOResponse
	{
		public string memory { get; set; }
		public string storage { get; set; }
		public string coresCount { get; set; }
	}
}
