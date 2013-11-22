using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class OperatingSystemDTOResponse : BaseDTOResponse
	{
		public string SystemMemory { get; set; }
		public string SystemStorage { get; set; }
		public string SystemCoresCount { get; set; }
	}
}
