package satori.session;

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
import org.apache.thrift.transport.TTransport;

import satori.common.SView;
import satori.config.SConfig;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskManager;
import satori.thrift.gen.User;

public class SSession {
	private final String host = SConfig.getHost();
	private final int thrift_port = SConfig.getThriftPort();
	private final int blobs_port = SConfig.getBlobsPort();
	private String username = null;
	private String password = null;
	private String token = "";
	private TTransport transport = null;
	private TProtocol protocol = null;
	
	public String getHost() { return host; }
	public int getBlobsPort() { return blobs_port; }
	public String getUsername() { return username; }
	public String getPassword() { return password; }
	
	private void createProtocol() throws Exception {
		SSLContext context = SSLContext.getInstance("TLSv1");
		context.init(null, new TrustManager[] { new X509TrustManager() {
			@Override public X509Certificate[] getAcceptedIssuers() { return null; }
			@Override public void checkClientTrusted(X509Certificate[] certs, String authType) {}
			@Override public void checkServerTrusted(X509Certificate[] certs, String authType) {}
		} }, new SecureRandom());
		SSLSocketFactory socket_factory = context.getSocketFactory();
		SSLSocket socket = (SSLSocket)socket_factory.createSocket(host, thrift_port);
		socket.setEnabledProtocols(new String[] { "TLSv1" });
		transport = new TFramedTransport(new TSocket(socket));
		protocol = new TBinaryProtocol(transport);
	}
	private void closeProtocol() { transport.close(); }
	
	private static volatile SSession instance = null;
	private static final List<SView> views = new ArrayList<SView>();
	
	private static class LoginTask implements STask {
		private final String username, password;
		public LoginTask(String username, String password) {
			this.username = username;
			this.password = password;
		}
		@Override public void run() throws Exception {
			SSession session = new SSession();
			STaskManager.log("Connecting to server...");
			session.createProtocol();
			STaskManager.log("Logging in to server...");
			User.Iface iface = new User.Client(session.protocol);
			session.token = iface.User_authenticate("", username, password);
			session.username = username;
			session.password = password;
			instance = session;
		}
	}
	private static class AnonymousLoginTask implements STask {
		@Override public void run() throws Exception {
			SSession session = new SSession();
			STaskManager.log("Connecting to server...");
			session.createProtocol();
			instance = session;
		}
	}
	
	public static void login(String username, String password) throws STaskException {
		if (instance != null) instance.closeProtocol();
		try { STaskManager.execute(new LoginTask(username, password)); }
		finally { updateViews(); }
	}
	public static void anonymousLogin() throws STaskException {
		if (instance != null) instance.closeProtocol();
		try { STaskManager.execute(new AnonymousLoginTask()); }
		finally { updateViews(); }
	}
	public static void logout() throws STaskException {
		if (instance != null) instance.closeProtocol();
		instance = null;
		updateViews();
	}
	
	public static SSession get() { return instance; }
	
	public static String getToken() throws Exception {
		SSession session = instance;
		if (session == null) throw new Exception("Not logged in");
		return session.token;
	}
	public static TProtocol getProtocol() throws Exception {
		SSession session = instance;
		if (session == null) throw new Exception("Not logged in");
		return session.protocol;
	}
	
	public static void addView(SView view) { views.add(view); }
	public static void removeView(SView view) { views.remove(view); }
	private static void updateViews() { for (SView view : views) view.update(); }
}
