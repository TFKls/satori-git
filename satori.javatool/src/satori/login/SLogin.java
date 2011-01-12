package satori.login;

import satori.common.SException;
import satori.thrift.SThriftClient;
import satori.thrift.SThriftCommand;
import satori.thrift.gen.User;

public class SLogin {
	private static String token = "";
	private static String username = null;
	private static String password = null;
	
	private static class LoginCommand implements SThriftCommand {
		private final String username, password;
		public LoginCommand(String username, String password) {
			this.username = username;
			this.password = password;
		}
		@Override public void call() throws Exception {
			User.Iface iface = new User.Client(SThriftClient.getProtocol());
			token = iface.User_authenticate(token, username, password);
		}
	}
	public static void login(String username, String password) throws SException {
		SThriftClient.setUpProtocol();
		SThriftClient.call(new LoginCommand(username, password));
		SLogin.username = username;
		SLogin.password = password;
	}
	
	/*public static void relogin() throws SException {
		login(username, password);
	}*/
	
	public static void logout() throws SException {
		//TODO: remote logout
		token = "";
		username = null;
		password = null;
	}
	
	public static String getToken() { return token; }
	public static String getLogin() { return username; }
	public static String getPassword() { return password; }
}
