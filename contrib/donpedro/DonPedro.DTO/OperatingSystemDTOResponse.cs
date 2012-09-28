using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class OperatingSystemDTOResponse : BaseDTOResponse
	{
		public string Memory { get; set; }
		public string Storage { get; set; }
		public string CoresCount { get; set; }
	}
}
