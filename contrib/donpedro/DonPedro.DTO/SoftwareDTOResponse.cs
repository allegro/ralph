using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class SoftwareDTOResponse : BaseDTOResponse
	{
	    public string Caption { get; set; }
	    public string Vendor { get; set; }
	    public string Version { get; set; }
	}
}
