package satori.config;

import java.util.prefs.Preferences;

public class SConfig {
	private static volatile String host = "satori.tcs.uj.edu.pl";
	private static volatile int thrift_port = 2889;
	private static volatile int blobs_port = 2887;
	private static volatile boolean has_config = false;
	
	public static String getHost() { return host; }
	public static int getThriftPort() { return thrift_port; }
	public static int getBlobsPort() { return blobs_port; }
	public static boolean hasConfig() { return has_config; }
	
	public static void load() {
		Preferences prefs = Preferences.userNodeForPackage(SConfig.class);
		host = prefs.get("host", host);
		thrift_port = Integer.valueOf(prefs.get("thrift port", String.valueOf(thrift_port)));
		blobs_port = Integer.valueOf(prefs.get("blobs port", String.valueOf(blobs_port)));
		has_config = "true".equals(prefs.get("has config", "false"));
	}
	public static void save(String host, int thrift_port, int blobs_port) {
		SConfig.host = host;
		SConfig.thrift_port = thrift_port;
		SConfig.blobs_port = blobs_port;
		Preferences prefs = Preferences.userNodeForPackage(SConfig.class);
		prefs.put("host", host);
		prefs.put("thrift port", String.valueOf(thrift_port));
		prefs.put("blobs port", String.valueOf(blobs_port));
		prefs.put("has config", "true");
		has_config = true;
	}
}
