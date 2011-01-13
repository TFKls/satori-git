package satori.server;

import java.util.HashMap;
import java.util.Map;

import satori.attribute.SAttributeReader;
import satori.blob.SBlobClient;
import satori.common.SAssert;
import satori.common.SException;
import satori.common.SFile;
import satori.login.SLogin;
import satori.thrift.SThriftClient;
import satori.thrift.SThriftCommand;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.Blob;

public class SAttributeData {
	static class AttributeWrap implements SAttributeReader {
		private Map<String, AnonymousAttribute> data;
		public AttributeWrap(Map<String, AnonymousAttribute> data) { this.data = data; }
		@Override public Iterable<String> getNames() { return data.keySet(); }
		@Override public boolean isBlob(String name) { return data.get(name).isIs_blob(); }
		@Override public String getString(String name) {
			AnonymousAttribute attr = data.get(name);
			if (attr.isIs_blob()) return null;
			return attr.getValue();
		}
		@Override public SFile getBlob(String name) {
			AnonymousAttribute attr = data.get(name);
			if (!attr.isIs_blob()) return null;
			return SFile.createRemote(attr.getFilename(), attr.getValue());
		}
	}
	static Map<String, AnonymousAttribute> createAttrMap(SAttributeReader attrs) {
		Map<String, AnonymousAttribute> map = new HashMap<String, AnonymousAttribute>();
		for (String name : attrs.getNames()) {
			if (attrs.isBlob(name)) {
				SFile file = attrs.getBlob(name);
				SAssert.assertTrue(file.isRemote(), "Non-remote blob");
				AnonymousAttribute attr = new AnonymousAttribute();
				attr.setIs_blob(true);
				attr.setFilename(file.getName());
				attr.setValue(file.getHash());
				map.put(name, attr);
			} else {
				AnonymousAttribute attr = new AnonymousAttribute();
				attr.setIs_blob(false);
				attr.setValue(attrs.getString(name));
				map.put(name, attr);
			}
		}
		return map;
	}
	
	private static class ExistsCommand implements SThriftCommand {
		private final String hash;
		private boolean result;
		public ExistsCommand(String hash) { this.hash = hash; }
		public boolean getResult() { return result; }
		@Override public void call() throws Exception {
			Blob.Iface iface = new Blob.Client(SThriftClient.getProtocol());
			result = iface.Blob_exists(SLogin.getToken(), hash);
		}
	}
	private static boolean checkBlobExists(SFile file) throws SException {
		ExistsCommand command = new ExistsCommand(file.getHash());
		SThriftClient.call(command);
		return command.getResult();
	}
	
	static void createBlobs(SAttributeReader test) throws SException {
		for (String name : test.getNames()) if (test.isBlob(name)) {
			SFile file = test.getBlob(name);
			//TODO: remove this remote stuff?
			if (file.isRemote()) continue;
			if (checkBlobExists(file)) file.markRemote();
			else file.markRemote(SBlobClient.putBlob(file.getFile()));
		}
	}
}
