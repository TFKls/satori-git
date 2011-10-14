package satori.data;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.common.SAssertException;
import satori.metadata.SMetadata;
import satori.session.SSession;
import satori.task.STaskHandler;
import satori.thrift.gen.AnonymousAttribute;
import satori.thrift.gen.Blob;

class SAttributeData {
	static AnonymousAttribute createAnonymousAttribute(Object value) {
		if (value instanceof String) {
			AnonymousAttribute result = new AnonymousAttribute();
			result.setIs_blob(false);
			result.setValue((String)value);
			return result;
		} else if (value instanceof SBlob) {
			AnonymousAttribute result = new AnonymousAttribute();
			result.setIs_blob(true);
			result.setFilename(((SBlob)value).getName());
			result.setValue(((SBlob)value).getHash());
			return result;
		} else throw new SAssertException("Invalid attribute class");
	}
	static Object convertAnonymousAttribute(AnonymousAttribute attr) {
		return attr.isIs_blob() ? SBlob.createRemote(attr.getFilename(), attr.getValue()) : attr.getValue();
	}
	
	static Map<String, AnonymousAttribute> convertAttrMap(Map<String, Object> attrs) {
		Map<String, AnonymousAttribute> map = new HashMap<String, AnonymousAttribute>();
		for (Map.Entry<String, Object> entry : attrs.entrySet()) {
			if (entry.getValue() instanceof String) {
				String str = (String)entry.getValue();
				AnonymousAttribute dst = new AnonymousAttribute();
				dst.setIs_blob(false);
				dst.setValue(str);
				map.put(entry.getKey(), dst);
			}
			if (entry.getValue() instanceof SBlob) {
				SBlob blob = (SBlob)entry.getValue();
				AnonymousAttribute dst = new AnonymousAttribute();
				dst.setIs_blob(true);
				dst.setFilename(blob.getName());
				dst.setValue(blob.getHash());
				map.put(entry.getKey(), dst);
			}
		}
		return map;
	}
	static Map<String, SBlob> getBlobAttrMap(Map<String, AnonymousAttribute> attrs) {
		Map<String, SBlob> result = new HashMap<String, SBlob>();
		for (Map.Entry<String, AnonymousAttribute> entry : attrs.entrySet()) {
			AnonymousAttribute attr = entry.getValue();
			if (!attr.isIs_blob()) continue; //TODO: do something better
			result.put(entry.getKey(), SBlob.createRemote(attr.getFilename(), attr.getValue()));
		}
		return result;
	}
	
	private static boolean checkBlobExists(STaskHandler handler, SBlob blob) throws Exception {
		handler.log("Checking blob existence...");
		Blob.Iface iface = new Blob.Client(handler.getProtocol());
		return iface.Blob_exists(SSession.getToken(), blob.getHash());
	}
	
	static Map<String, Object> createRemoteAttrMap(Map<? extends SMetadata, Object> attrs) {
		Map<String, Object> result = new HashMap<String, Object>();
		for (Map.Entry<? extends SMetadata, Object> entry : attrs.entrySet()) {
			String key = entry.getKey().getName();
			Object value = entry.getValue();
			result.put(key, value);
		}
		return result;
	}
	static <T extends SMetadata> Map<T, Object> createLocalAttrMap(List<T> meta_list, Map<String, AnonymousAttribute> attrs) {
		Map<T, Object> result = new HashMap<T, Object>();
		for (T meta : meta_list) {
			AnonymousAttribute attr = attrs.get(meta.getName());
			if (attr == null) continue;
			Object value = attr.isIs_blob() ? SBlob.createRemote(attr.getFilename(), attr.getValue()) : attr.getValue();
			result.put(meta, value);
		}
		return result;
	}
	
	static void createBlobs(STaskHandler handler, Map<String, Object> attrs) throws Exception {
		for (Object value : attrs.values()) {
			if (!(value instanceof SBlob)) continue;
			SBlob blob = (SBlob)value;
			if (!checkBlobExists(handler, blob)) blob.saveRemoteTask(handler);
		}
	}
}
