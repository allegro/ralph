using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class ProcessorDTOResponse : BaseDTOResponse
	{
		public string speed { get; set; }
		public string cores { get; set; }
		public string index { get; set; }
		public string description { get; set; }
		public string number_of_logical_processors { get; set; }
		public string caption { get; set; }
	}
}
