using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class SoftwareDTOResponse : BaseDTOResponse
	{
		public string Label { get; set; }
	    public string Version { get; set; }
	    public string Path { get; set; }
	    public string ModelName { get; set; }
	}
}
