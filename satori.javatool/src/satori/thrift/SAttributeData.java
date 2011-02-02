package satori.thrift;

import java.util.HashMap;
import java.util.Map;

import satori.attribute.SAttribute;
import satori.attribute.SAttributeReader;
import satori.attribute.SBlobAttribute;
import satori.attribute.SStringAttribute;
import satori.blob.SBlob;
import satori.common.SException;
import satori.session.SSession;
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
		@Override public SBlob getBlob(String name) {
			AnonymousAttribute attr = data.get(name);
			if (!attr.isIs_blob()) return null;
			return SBlob.createRemote(attr.getFilename(), attr.getValue());
		}
		@Override public Map<String, SAttribute> getMap() {
			Map<String, SAttribute> result = new HashMap<String, SAttribute>();
			for (String name : getNames()) {
				if (isBlob(name)) result.put(name, new SBlobAttribute(getBlob(name)));
				else result.put(name, new SStringAttribute(getString(name)));
			}
			return result;
		}
	}
	static Map<String, AnonymousAttribute> createAttrMap(SAttributeReader attrs) {
		Map<String, AnonymousAttribute> map = new HashMap<String, AnonymousAttribute>();
		for (String name : attrs.getNames()) {
			if (attrs.isBlob(name)) {
				SBlob blob = attrs.getBlob(name);
				AnonymousAttribute attr = new AnonymousAttribute();
				attr.setIs_blob(true);
				attr.setFilename(blob.getName());
				attr.setValue(blob.getHash());
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
			result = iface.Blob_exists(SSession.getToken(), hash);
		}
	}
	private static boolean checkBlobExists(SBlob blob) throws SException {
		ExistsCommand command = new ExistsCommand(blob.getHash());
		SThriftClient.call(command);
		return command.getResult();
	}
	
	static void createBlobs(SAttributeReader test) throws SException {
		for (String name : test.getNames()) if (test.isBlob(name)) {
			SBlob blob = test.getBlob(name);
			if (!checkBlobExists(blob)) blob.saveRemote();
		}
	}
}
