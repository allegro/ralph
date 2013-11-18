using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class ProcessorDTOResponse : BaseDTOResponse
	{
		public string Speed { get; set; }
		public string Cores { get; set; }
		public string Index { get; set; }
		public string Description { get; set; }
		public string NumberOfLogicalProcessors { get; set; }
		public string Caption { get; set; }
		public string Manufacturer { get; set; }
		public string Version { get; set; }
		public string Is64Bit { get; set; }
	}
}
