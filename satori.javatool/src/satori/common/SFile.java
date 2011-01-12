package satori.common;

import java.io.File;

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
	
	public static SFile createLocal(File file) {
		SFile self = new SFile();
		self.name = file.getName();
		self.hash = null;
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
	
	public void markRemote(String new_hash) {
		if (hash != null && !hash.equals(new_hash)) throw new RuntimeException("Hash codes don't match");
		hash = new_hash;
		remote = true;
	}
	public void update(SFile other) {
		if (!name.equals(other.name)) throw new RuntimeException("File names don't match"); 
		if (hash != null && other.hash != null && !hash.equals(other.hash)) throw new RuntimeException("Hash codes don't match");
		if (file == null && other.file != null) file = other.file;
		if (other.remote) remote = true; 
	}
	public boolean check(SFile other) {
		if (!name.equals(other.name)) return true;
		if (hash != null && other.hash != null) {
			if (!hash.equals(other.hash)) return true;
			if (file == null && other.file != null) file = other.file;
			if (other.remote) remote = true;
			return false;
		}
		if (file != null && other.file != null) {
			if (!file.equals(other.file)) return true;
			if (hash == null && other.hash != null) hash = other.hash;
			if (other.remote) remote = true;
			return false;
		}
		return true;
	}
}
