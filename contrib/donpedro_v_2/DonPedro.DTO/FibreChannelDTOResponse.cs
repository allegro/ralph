using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class FibreChannelDTOResponse : BaseDTOResponse
	{
		public string PhysicalId { get; set; }
		public string Label { get; set; }
		public string ModelName { get; set; }
	}
}
