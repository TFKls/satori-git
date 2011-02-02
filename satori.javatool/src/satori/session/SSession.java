package satori.session;

import satori.common.SException;
import satori.config.SConfig;
import satori.thrift.SThriftClient;
import satori.thrift.SThriftCommand;
import satori.thrift.gen.User;

public class SSession {
	private String host;
	private int thrift_port;
	private int blobs_port;
	private String username;
	private String password;
	private String token;
	
	private static SSession instance = null;
	
	public static void connect() throws SException {
		instance = new SSession();
		instance.host = SConfig.getHost();
		instance.thrift_port = SConfig.getThriftPort();
		instance.blobs_port = SConfig.getBlobsPort();
		instance.username = null;
		instance.password = null;
		instance.token = "";
		SThriftClient.setUpProtocol();
	}
	public static void disconnect() {
		SThriftClient.closeProtocol();
		instance = null;
	}
	
	private static class LoginCommand implements SThriftCommand {
		private final String username, password;
		public LoginCommand(String username, String password) {
			this.username = username;
			this.password = password;
		}
		@Override public void call() throws Exception {
			User.Iface iface = new User.Client(SThriftClient.getProtocol());
			instance.token = iface.User_authenticate("", username, password);
		}
	}
	public static void login(String username, String password) throws SException {
		connect();
		SThriftClient.call(new LoginCommand(username, password));
		instance.username = username;
		instance.password = password;
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
