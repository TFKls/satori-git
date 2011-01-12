package satori.thrift;

import org.apache.thrift.TException;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;
import org.apache.thrift.transport.TFramedTransport;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.transport.TTransport;

import satori.common.SException;
import satori.config.SConfig;

public class SThriftClient {
	private static TTransport transport = null;
	private static TProtocol protocol = null;
	
	public static void setUpProtocol() throws SException {
		if (transport != null) transport.close();
		transport = new TFramedTransport(new TSocket(SConfig.getHost(), SConfig.getThriftPort()));
		try { transport.open(); }
		catch(TException ex) { throw new SException(ex); }
		protocol = new TBinaryProtocol(transport);
	}
	
	public static TProtocol getProtocol() throws SException {
		if (protocol == null) setUpProtocol();
		return protocol;
	}
	
	public static void call(SThriftCommand command) throws SException {
		try { command.call(); }
		catch(RuntimeException ex) { throw ex; }
		catch(Exception ex) { throw new SException(ex); }
	}
}
