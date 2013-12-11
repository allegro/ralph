using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class ProcessorDTOResponse : BaseDTOResponse
	{
		public string ModelName { get; set; }
		public string Speed { get; set; }
		public string Cores { get; set; }
		public string Index { get; set; }
		public string Family { get; set; }
		public string Label { get; set; }
	}
}
