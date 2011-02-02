package satori.blob;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.IOUtils;

import satori.common.SException;

public class SBlob {
	private String name;
	private String hash;
	private File file;
	
	public String getName() { return name; }
	public String getHash() { return hash; }
	public File getFile() { return file; }
	
	public boolean equals(SBlob other) {
		if (name == null && other.name != null) return false;
		if (name != null && !name.equals(other.name)) return false;
		if (hash == null && other.hash != null) return false;
		if (hash != null && !hash.equals(other.hash)) return false;
		if (file == null && other.file != null) return false;
		if (file != null && !file.equals(other.file)) return false;
		return true;
	}
	@Override public boolean equals(Object other) {
		if (!(other instanceof SBlob)) return false;
		return equals((SBlob)other);
	}
	@Override public int hashCode() {
		int result = 0;
		if (name != null) result ^= name.hashCode();
		if (hash != null) result ^= hash.hashCode();
		if (file != null) result ^= file.hashCode();
		return result;
	}
	
	private SBlob() {}
	
	private static String computeHash(File file) throws SException {
		byte[] bin_hash;
		try { bin_hash = DigestUtils.sha384(new FileInputStream(file)); }
		catch(IOException ex) { throw new SException(ex); }
		return Base64.encodeBase64URLSafeString(bin_hash);
	}
	private static void copy(File src, File dst) throws IOException {
		InputStream in = null;
		OutputStream out = null;
		try {
			in = new FileInputStream(src);
			out = new FileOutputStream(dst);
			IOUtils.copy(in, out);
		} finally {
			IOUtils.closeQuietly(in);
			IOUtils.closeQuietly(out);
		}
	}
	
	public static SBlob createLocal(File file) throws SException {
		SBlob self = new SBlob();
		self.name = file.getName();
		self.hash = computeHash(file);
		self.file = file;
		return self;
	}
	public static SBlob createRemote(String name, String hash) {
		SBlob self = new SBlob();
		self.name = name;
		self.hash = hash;
		self.file = null;
		return self;
	}
	
	public SBlob rename(String name) {
		if (name.equals(this.name)) return this;
		SBlob result = new SBlob();
		result.name = name;
		result.hash = hash;
		result.file = file;
		return result;
	}
	
	public void saveLocal(File dst) throws SException {
		if (dst.equals(file)) return;
		if (file == null) SBlobClient.getBlob(hash, dst);
		else {
			try { copy(file, dst); }
			catch(IOException ex) { throw new SException(ex); }
		}
	}
	public void saveRemote() throws SException {
		String remote_hash = SBlobClient.putBlob(file);
		if (remote_hash != hash) {
			hash = remote_hash;
			throw new SException("Hash codes don't match. Perhaps the local file has been modified");
		}
	}
}
