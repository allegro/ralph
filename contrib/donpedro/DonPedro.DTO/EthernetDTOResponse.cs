/*
 * Created by SharpDevelop.
 * User: Andrzej Jankowski
 * Date: 9/25/2012
 * Time: 11:35 PM
 * 
 */
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
