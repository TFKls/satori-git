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

import satori.common.SAssert;
import satori.common.SException;

public class SBlob {
	private String name;
	private String hash;
	private File file;
	private boolean remote;
	
	public String getName() { return name; }
	public String getHash() { return hash; }
	public File getFile() { return file; }
	public boolean isRemote() { return remote; }
	
	/*public boolean equals(SBlob data) {
		if (name == null && data.name != null) return false;
		if (name != null && !name.equals(data.name)) return false;
		if (hash == null && data.hash != null) return false;
		if (hash != null && !hash.equals(data.hash)) return false;
		if (file == null && data.file != null) return false;
		if (file != null && !file.equals(data.file)) return false;
		if (remote != data.remote) return false;
		return true;
	}
	@Override public boolean equals(Object arg) {
		if (!(arg instanceof SFile)) return false;
		return equals((SBlob)arg);
	}
	@Override public int hashCode() {
		int result = 0;
		if (name != null) result ^= name.hashCode();
		if (hash != null) result ^= hash.hashCode();
		if (file != null) result ^= file.hashCode();
		return result;
	}*/
	
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
		self.remote = false;
		return self;
	}
	public static SBlob createRemote(String name, String hash) {
		SBlob self = new SBlob();
		self.name = name;
		self.hash = hash;
		self.file = null;
		self.remote = true;
		return self;
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
		SAssert.assertEquals(hash, remote_hash, "Hash codes don't match");
		remote = true;
	}
	public void markRemote() { remote = true; }
	
	public void update(SBlob other) {
		SAssert.assertEquals(name, other.name, "File names don't match"); 
		SAssert.assertEquals(hash, other.hash, "Hash codes don't match");
		if (file == null && other.file != null) file = other.file; //TODO: ?
		if (other.remote) remote = true; 
	}
	public boolean check(SBlob other) {
		if (!name.equals(other.name)) return true;
		if (!hash.equals(other.hash)) return true;
		if (file == null && other.file != null) file = other.file; //TODO: ?
		if (other.remote) remote = true;
		return false;
	}
}
