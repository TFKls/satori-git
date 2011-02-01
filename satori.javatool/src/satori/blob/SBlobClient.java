package satori.blob;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.StringWriter;
import java.io.Writer;
import java.net.HttpURLConnection;
import java.net.URL;

import org.apache.commons.io.IOUtils;

import satori.common.SException;
import satori.config.SConfig;
import satori.login.SLogin;

public class SBlobClient {
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
			InputStream file_in = null;
			OutputStream conn_out = null;
			try {
				file_in = new FileInputStream(file);
				conn_out = connection.getOutputStream();
				IOUtils.copy(file_in, conn_out);
			} finally {
				IOUtils.closeQuietly(file_in);
				IOUtils.closeQuietly(conn_out);
			}
			int response = connection.getResponseCode();
			if (response != HttpURLConnection.HTTP_OK) throw new SException("Error saving blob: " + response + " " + connection.getResponseMessage());
			InputStream conn_in = null;
			Writer result = new StringWriter();
			try {
				conn_in = connection.getInputStream();
				IOUtils.copy(conn_in, result);
			} finally {
				IOUtils.closeQuietly(conn_in);
			}
			return result.toString();
		}
		catch(IOException ex) { throw new SException(ex); }
	}
	
	private static void getBlobAux(String address, File file) throws SException {
		try {
			URL url = new URL(address);
			HttpURLConnection connection = (HttpURLConnection)url.openConnection();
			connection.setUseCaches(false);
			connection.setRequestMethod("GET");
			connection.setRequestProperty("Cookie", "satori_token=" + SLogin.getToken());
			connection.setRequestProperty("Content-length", "0");
			int response = connection.getResponseCode();
			if (response != HttpURLConnection.HTTP_OK) throw new SException("Error loading blob: " + response + " " + connection.getResponseMessage());
			InputStream conn_in = null;
			OutputStream file_out = null;
			try {
				conn_in = connection.getInputStream();
				file_out = new FileOutputStream(file);
				IOUtils.copy(conn_in, file_out);
			} finally {
				IOUtils.closeQuietly(conn_in);
				IOUtils.closeQuietly(file_out);
			}
		}
		catch(IOException ex) { throw new SException(ex); }
	}
	
	public static String putBlob(File file) throws SException {
		String address = "http://" + SConfig.getHost() + ":" + SConfig.getBlobsPort() + "/blob/upload";
		return putBlob(address, file);
	}
	public static void getBlob(String hash, File file) throws SException {
		String address = "http://" + SConfig.getHost() + ":" + SConfig.getBlobsPort() + "/blob/download/" + hash;
		getBlobAux(address, file);
	}
}
