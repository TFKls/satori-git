package satori.config;

import java.util.prefs.Preferences;

public class SConfig {
	private static volatile String host = "satori.tcs.uj.edu.pl";
	private static volatile int thrift_port = 2889;
	private static volatile int blobs_port = 2887;
	private static volatile boolean use_ssl = true;
	private static volatile boolean has_config = false;
	
	public static String getHost() { return host; }
	public static int getThriftPort() { return thrift_port; }
	public static int getBlobsPort() { return blobs_port; }
	public static boolean getUseSSL() { return use_ssl; }
	public static boolean hasConfig() { return has_config; }
	
	public static void setHost(String host) { SConfig.host = host; }
	public static void setThriftPort(int port) { thrift_port = port; }
	public static void setBlobsPort(int port) { blobs_port = port; }
	public static void setUseSSL(boolean use_ssl) { SConfig.use_ssl = use_ssl; }
	
	public static void load() {
		Preferences prefs = Preferences.userNodeForPackage(SConfig.class);
		host = prefs.get("host", host);
		thrift_port = Integer.valueOf(prefs.get("thrift port", String.valueOf(thrift_port)));
		blobs_port = Integer.valueOf(prefs.get("blobs port", String.valueOf(blobs_port)));
		use_ssl = Boolean.valueOf(prefs.get("use ssl", String.valueOf(use_ssl)));
		has_config = Boolean.valueOf(prefs.get("has config", "false"));
	}
	public static void save() {
		Preferences prefs = Preferences.userNodeForPackage(SConfig.class);
		prefs.put("host", host);
		prefs.put("thrift port", String.valueOf(thrift_port));
		prefs.put("blobs port", String.valueOf(blobs_port));
		prefs.put("use ssl", String.valueOf(use_ssl));
		prefs.put("has config", "true");
		has_config = true;
	}
}
