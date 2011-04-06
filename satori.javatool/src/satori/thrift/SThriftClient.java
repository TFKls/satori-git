package satori.thrift;

import org.apache.thrift.protocol.TProtocol;

import satori.common.SException;
import satori.session.SSession;

@Deprecated public class SThriftClient {
	public static TProtocol getProtocol() throws SException { return SSession.getProtocol(); }
	
	public static void call(SThriftCommand command) throws SException {
		try { command.call(); }
		catch(RuntimeException ex) { throw ex; }
		catch(Exception ex) { throw new SException(ex); }
	}
}
