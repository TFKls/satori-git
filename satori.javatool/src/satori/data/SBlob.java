package satori.data;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.IOUtils;

import satori.task.SResultTask;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskHandler;

public class SBlob {
	private String name;
	private String hash;
	private File file;
	
	public String getName() { return name; }
	public String getHash() { return hash; }
	public File getFile() { return file; }
	
	private boolean equalsAux(SBlob other) {
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
		return equalsAux((SBlob)other);
	}
	@Override public int hashCode() {
		int result = 0;
		if (name != null) result ^= name.hashCode();
		if (hash != null) result ^= hash.hashCode();
		if (file != null) result ^= file.hashCode();
		return result;
	}
	
	private SBlob() {}
	
	public static SBlob createRemote(String name, String hash) {
		SBlob self = new SBlob();
		self.name = name;
		self.hash = hash;
		self.file = null;
		return self;
	}
	
	private static String computeHashTask(STaskHandler handler, File file) throws Exception {
		handler.log("Computing hash code...");
		byte[] bin_hash = DigestUtils.sha384(new FileInputStream(file));
		return Base64.encodeBase64URLSafeString(bin_hash);
	}
	public static SBlob createLocalTask(STaskHandler handler, File file) throws Exception {
		SBlob self = new SBlob();
		self.name = file.getName();
		self.hash = computeHashTask(handler, file);
		self.file = file;
		return self;
	}
	public static SBlob createLocal(final STaskHandler handler, final File file) throws STaskException {
		return handler.execute(new SResultTask<SBlob>() {
			@Override public SBlob run() throws Exception { return createLocalTask(handler, file); }
		});
	}
	
	public InputStream getStreamTask() throws Exception {
		if (file != null) return new FileInputStream(file);
		else return SBlobClient.getBlobStream(hash);
	}
	
	public SBlob rename(String name) {
		if (name.equals(this.name)) return this;
		SBlob result = new SBlob();
		result.name = name;
		result.hash = hash;
		result.file = file;
		return result;
	}
	
	private static void copyTask(STaskHandler handler, File src, File dst) throws Exception {
		handler.log("Copying local file...");
		InputStream in = new FileInputStream(src);
		try {
			OutputStream out = new FileOutputStream(dst);
			try { IOUtils.copy(in, out); }
			finally { IOUtils.closeQuietly(out); }
		} finally { IOUtils.closeQuietly(in); }
	}
	
	public void saveLocalTask(STaskHandler handler, File dst) throws Exception {
		if (dst.equals(file)) return;
		if (file != null) copyTask(handler, file, dst);
		else SBlobClient.getBlob(handler, hash, dst);
	}
	public void saveRemoteTask(STaskHandler handler) throws Exception {
		String remote_hash = SBlobClient.putBlob(handler, file);
		if (!remote_hash.equals(hash)) throw new Exception("Hash codes don't match. Load the local file again");
	}
	
	public void saveLocal(final STaskHandler handler, final File dst) throws STaskException {
		if (dst.equals(file)) return;
		handler.execute(new STask() {
			@Override public void run() throws Exception {  saveLocalTask(handler, dst); }
		});
	}
	public void saveRemote(final STaskHandler handler) throws STaskException {
		handler.execute(new STask() {
			@Override public void run() throws Exception { saveRemoteTask(handler); }
		});
	}
}
