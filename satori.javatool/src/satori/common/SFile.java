package satori.common;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.digest.DigestUtils;

public class SFile {
	private String name;
	private String hash;
	private File file;
	private boolean remote;
	
	public String getName() { return name; }
	public String getHash() { return hash; }
	public File getFile() { return file; }
	public boolean isRemote() { return remote; }
	
	/*public boolean equals(SFile data) {
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
		return equals((SFile)arg);
	}
	@Override public int hashCode() {
		int result = 0;
		if (name != null) result ^= name.hashCode();
		if (hash != null) result ^= hash.hashCode();
		if (file != null) result ^= file.hashCode();
		return result;
	}*/
	
	private SFile() {}
	
	private static String computeHash(File file) throws SException {
		byte[] bin_hash;
		try { bin_hash = DigestUtils.sha384(new FileInputStream(file)); }
		catch(IOException ex) { throw new SException(ex); }
		return Base64.encodeBase64URLSafeString(bin_hash);
	}
	
	public static SFile createLocal(File file) throws SException {
		SFile self = new SFile();
		self.name = file.getName();
		self.hash = computeHash(file);
		self.file = file;
		self.remote = false;
		return self;
	}
	public static SFile createRemote(String name, String hash) {
		SFile self = new SFile();
		self.name = name;
		self.hash = hash;
		self.file = null;
		self.remote = true;
		return self;
	}
	
	public void markRemote() { remote = true; }
	public void markRemote(String new_hash) {
		SAssert.assertEquals(hash, new_hash, "Hash codes don't match");
		remote = true;
	}
	public void update(SFile other) {
		SAssert.assertEquals(name, other.name, "File names don't match"); 
		SAssert.assertEquals(hash, other.hash, "Hash codes don't match");
		if (file == null && other.file != null) file = other.file; //TODO: ?
		if (other.remote) remote = true; 
	}
	public boolean check(SFile other) {
		if (!name.equals(other.name)) return true;
		if (!hash.equals(other.hash)) return true;
		if (file == null && other.file != null) file = other.file; //TODO: ?
		if (other.remote) remote = true;
		return false;
	}
}
