/*
 * Created by SharpDevelop.
 * User: Andrzej Jankowski
 * Date: 9/25/2012
 * Time: 11:31 PM
 * 
 */
using System;
using DonPedro.DTO;

namespace DonPedro.DTO
{
	public class MemoryDTOResponse : BaseDTOResponse
	{
		public string size { get; set; }
		public string speed { get; set; }
		public string index { get; set; }
		public string sn { get; set; }
		public string caption { get; set; }
	}
}
