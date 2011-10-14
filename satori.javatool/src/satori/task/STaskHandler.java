package satori.task;

import org.apache.thrift.protocol.TProtocol;

public interface STaskHandler {
	TProtocol getProtocol() throws Exception;
	
	void log(String message);
	void execute(STask task) throws STaskException;
	<T> T execute(SResultTask<T> task) throws STaskException;
	
	void close();
}
