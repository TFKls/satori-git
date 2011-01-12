package satori.blob;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.Reader;
import java.io.StringWriter;
import java.io.Writer;
import java.net.HttpURLConnection;
import java.net.URL;

import satori.common.SException;
import satori.config.SConfig;
import satori.login.SLogin;

public class SBlobClient {
	private static void transfer(InputStream input, OutputStream output) throws IOException {
		byte[] buffer = new byte[4096];
		int length;
		while ((length = input.read(buffer)) != -1) output.write(buffer, 0, length);
		output.flush();
	}
	private static void transfer(Reader input, Writer output) throws IOException {
		char[] buffer = new char[4096];
		int length;
		while ((length = input.read(buffer)) != -1) output.write(buffer, 0, length);
		output.flush();
	}
	
	private static String putBlob(String address, File file) throws SException {
		try {
			URL url = new URL(address);
			HttpURLConnection connection = (HttpURLConnection)url.openConnection();
			connection.setDoOutput(true);
			connection.setUseCaches(false);
			connection.setRequestMethod("PUT");
			connection.setRequestProperty("Cookie", "satori_token=" + SLogin.getToken());
			connection.setRequestProperty("Content-length", String.valueOf(file.length()));
			connection.setRequestProperty("Filename", file.getName());
			InputStream file_is = new FileInputStream(file);
			try {
				OutputStream output = connection.getOutputStream();
				try { transfer(file_is, output); }
				finally { output.close(); }
			}
			finally { file_is.close(); }
			int response = connection.getResponseCode();
			if (response != HttpURLConnection.HTTP_OK) throw new SException("Error saving blob: " + response + " " + connection.getResponseMessage());
			Writer output = new StringWriter();
			Reader input = new BufferedReader(new InputStreamReader(connection.getInputStream()));
			try { transfer(input, output); }
			finally { input.close(); }
			return output.toString();
		}
		catch(IOException ex) { throw new SException(ex); }
	}
	
	/*public static String putBlob(String model, long id, String oa_group, String oa_name, File file) throws SException {
		String address = "http://" + SGlobal.getHost() + ":" + SGlobal.getBlobPort() + "/blob/" + model + "/" + id + "/" + oa_group + "/" + oa_name;
		return putBlob(address, file);
	}*/
	public static String putBlob(File file) throws SException {
		String address = "http://" + SConfig.getHost() + ":" + SConfig.getBlobsPort() + "/blob/upload";
		return putBlob(address, file);
	}
}
