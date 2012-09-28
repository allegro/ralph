using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class EthernetDTOResponse : BaseDTOResponse
	{
		public string Mac { get; set; }
		public string Speed { get; set; }
	}
}
