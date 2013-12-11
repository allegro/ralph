using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class MemoryDTOResponse : BaseDTOResponse
	{
		public string Label { get; set; }
		public string Size { get; set; }
		public string Speed { get; set; }
		public string Index { get; set; }
	}
}
