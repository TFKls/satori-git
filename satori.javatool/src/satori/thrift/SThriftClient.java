package satori.thrift;

import java.io.IOException;
import java.net.Socket;

import javax.net.SocketFactory;
import javax.net.ssl.SSLSocketFactory;

import org.apache.thrift.TException;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;
import org.apache.thrift.transport.TFramedTransport;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.transport.TTransport;

import satori.common.SException;
import satori.session.SSession;

public class SThriftClient {
	private static TTransport transport = null;
	private static TProtocol protocol = null;
	
	public static void setUpProtocol() throws SException {
		if (transport != null) transport.close();
		SSession.ensureConnected();
		SocketFactory socket_factory = SSLSocketFactory.getDefault();
		Socket socket;
		try { socket = socket_factory.createSocket(SSession.getHost(), SSession.getThriftPort()); }
		catch(IOException ex) { throw new SException(ex); }
		try { transport = new TFramedTransport(new TSocket(socket)); }
		catch(TException ex) { throw new SException(ex); }
		/*try { transport.open(); }
		catch(TException ex) { throw new SException(ex); }*/
		protocol = new TBinaryProtocol(transport);
	}
	public static void closeProtocol() {
		protocol = null;
		if (transport != null) transport.close();
		transport = null;
	}
	
	public static TProtocol getProtocol() throws SException {
		if (protocol == null) throw new SException("Thrift protocol not set");
		return protocol;
	}
	
	public static void call(SThriftCommand command) throws SException {
		try { command.call(); }
		catch(RuntimeException ex) { throw ex; }
		catch(Exception ex) { throw new SException(ex); }
	}
}
