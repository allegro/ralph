using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class FibreChannelDTOResponse : BaseDTOResponse
	{
		public string PhysicalId { get; set; }
		public string Model { get; set; }
		public string Sn { get; set; }
		public string Manufacturer { get; set; }
	}
}
