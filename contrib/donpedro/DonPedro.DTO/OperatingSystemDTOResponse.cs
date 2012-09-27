using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class OperatingSystemResponseDTO : BaseDTOResponse
	{
		public string memory { get; set; }
		public string storage { get; set; }
		public string cores_count { get; set; }
	}
}
