using System;
using System.Runtime.Serialization;

namespace DonPedro.Detectors.Exceptions
{
	public class ExternalCommandExecutionException : Exception, ISerializable
	{
		public ExternalCommandExecutionException(string message) : base(message)
		{
		}
	}
}