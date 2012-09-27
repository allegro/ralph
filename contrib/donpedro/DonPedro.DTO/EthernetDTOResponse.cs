using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class EthernetDTOResponse : BaseDTOResponse
	{
		public string mac { get; set; }
		public string speed { get; set; }
	}
}
