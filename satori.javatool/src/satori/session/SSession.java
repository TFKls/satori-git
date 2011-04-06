package satori.session;

import satori.common.SException;
import satori.config.SConfig;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskLogger;
import satori.task.STaskManager;
import satori.thrift.SThriftClient;
import satori.thrift.gen.User;

public class SSession {
	private volatile String host;
	private volatile int thrift_port;
	private volatile int blobs_port;
	private volatile String username;
	private volatile String password;
	private volatile String token;
	
	private static volatile SSession instance = null;
	
	private static void connect() throws SException {
		instance = new SSession();
		instance.host = SConfig.getHost();
		instance.thrift_port = SConfig.getThriftPort();
		instance.blobs_port = SConfig.getBlobsPort();
		instance.username = null;
		instance.password = null;
		instance.token = "";
		SThriftClient.setUpProtocol();
	}
	private static void disconnect() {
		SThriftClient.closeProtocol();
		instance = null;
	}
	
	private static class LoginTask implements STask {
		private final String username, password;
		public LoginTask(String username, String password) {
			this.username = username;
			this.password = password;
		}
		@Override public void run(STaskLogger logger) throws Throwable {
			logger.log("Creating session...");
			connect();
			logger.log("Logging in...");
			User.Iface iface = new User.Client(SThriftClient.getProtocol());
			instance.token = iface.User_authenticate("", username, password);
			instance.username = username;
			instance.password = password;
		}
	}
	public static void login(String username, String password) throws STaskException {
		STaskManager.execute(new LoginTask(username, password));
	}
	
	private static class AnonymousLoginTask implements STask {
		@Override public void run(STaskLogger logger) throws Throwable {
			logger.log("Creating session...");
			connect();
		}
	}
	public static void anonymousLogin() throws STaskException {
		STaskManager.execute(new AnonymousLoginTask());
	}
	
	private static class LogoutTask implements STask {
		@Override public void run(STaskLogger logger) throws Throwable {
			logger.log("Closing session...");
			disconnect();
		}
	}
	public static void logout() throws STaskException {
		STaskManager.execute(new LogoutTask());
	}
	
	public static boolean isConnected() { return instance != null; }
	public static void ensureConnected() throws SException {
		if (instance == null) throw new SException("Not logged in");
	}
	
	public static String getHost() { return instance.host; }
	public static int getThriftPort() { return instance.thrift_port; }
	public static int getBlobsPort() { return instance.blobs_port; }
	
	public static boolean hasLogin() {
		if (!isConnected()) return false;
		return instance.username != null;
	}
	public static String getLogin() {
		if (!isConnected()) return null;
		return instance.username;
	}
	public static String getPassword() {
		if (!isConnected()) return null;
		return instance.password;
	}
	public static String getToken() throws SException {
		ensureConnected();
		return instance.token;
	}
}
