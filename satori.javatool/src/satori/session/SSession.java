package satori.session;

import java.net.Socket;
import java.security.SecureRandom;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.List;

import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;
import org.apache.thrift.transport.TFramedTransport;
import org.apache.thrift.transport.TSocket;

import satori.common.SView;
import satori.config.SConfig;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskHandler;
import satori.thrift.gen.User;

public class SSession {
	private String username = null;
	private String password = null;
	private String token = "";
	
	private static Socket createUnsecureSocket() throws Exception {
		return new Socket(SConfig.getHost(), SConfig.getThriftPort());
	}
	private static Socket createSecureSocket() throws Exception {
		SSLContext context = SSLContext.getInstance("TLSv1");
		context.init(null, new TrustManager[] { new X509TrustManager() {
			@Override public X509Certificate[] getAcceptedIssuers() { return null; }
			@Override public void checkClientTrusted(X509Certificate[] certs, String authType) {}
			@Override public void checkServerTrusted(X509Certificate[] certs, String authType) {}
		} }, new SecureRandom());
		SSLSocketFactory socket_factory = context.getSocketFactory();
		SSLSocket socket = (SSLSocket)socket_factory.createSocket(SConfig.getHost(), SConfig.getThriftPort());
		socket.setEnabledProtocols(new String[] { "TLSv1" });
		return socket;
	}
	public static TProtocol getProtocol(STaskHandler handler) throws Exception {
		handler.log("Connecting to server...");
		Socket socket = SConfig.getUseSSL() ? createSecureSocket() : createUnsecureSocket();
		socket.setSoTimeout(10000);
		return new TBinaryProtocol(new TFramedTransport(new TSocket(socket)));
	}
	public static void closeProtocol(TProtocol protocol) { protocol.getTransport().close(); }
	
	private static volatile SSession instance = new SSession();
	private static final List<SView> views = new ArrayList<SView>();
	
	private static class LoginTask implements STask {
		private final STaskHandler handler;
		private final String username, password;
		public LoginTask(STaskHandler handler, String username, String password) {
			this.handler = handler;
			this.username = username;
			this.password = password;
		}
		@Override public void run() throws Exception {
			SSession session = new SSession();
			handler.log("Logging in to server...");
			User.Iface iface = new User.Client(handler.getProtocol());
			session.token = iface.User_authenticate("", username, password);
			session.username = username;
			session.password = password;
			instance = session;
		}
	}
	
	public static void login(STaskHandler handler, String username, String password) throws STaskException {
		handler.execute(new LoginTask(handler, username, password));
		updateViews();
	}
	public static void anonymousLogin(STaskHandler handler) {
		instance = new SSession();
		updateViews();
	}
	public static void logout() {
		instance = new SSession();
		updateViews();
	}
	
	public static String getToken() { return instance.token; }
	public static String getUsername() { return instance.username; }
	public static String getPassword() { return instance.password; }	
	
	public static void addView(SView view) { views.add(view); }
	public static void removeView(SView view) { views.remove(view); }
	private static void updateViews() { for (SView view : views) view.update(); }
}
