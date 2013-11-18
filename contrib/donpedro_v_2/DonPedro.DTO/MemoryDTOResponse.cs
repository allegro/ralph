using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class MemoryDTOResponse : BaseDTOResponse
	{
		public string Size { get; set; }
		public string Speed { get; set; }
		public string Index { get; set; }
		public string Sn { get; set; }
		public string Caption { get; set; }
	}
}
