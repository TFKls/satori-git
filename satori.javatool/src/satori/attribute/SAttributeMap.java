package satori.attribute;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import satori.blob.SBlob;

public class SAttributeMap implements SAttributeReader {
	private Map<String, SAttribute> map = new HashMap<String, SAttribute>();
	
	private SAttributeMap() {}
	
	public static SAttributeMap create(SAttributeReader source) {
		//if (source == null) return null; //TODO: ?
		SAttributeMap self = new SAttributeMap();
		for (String name : source.getNames()) {
			if (source.isBlob(name)) self.map.put(name, new SBlobAttribute(source.getBlob(name)));
			else self.map.put(name, new SStringAttribute(source.getString(name)));
		}
		return self;
	}
	public static SAttributeMap createEmpty() {
		return new SAttributeMap();
	}
	
	/*@Override public boolean equals(Object arg) {
		if (!(arg instanceof SAttributeMap)) return false;
		return map.equals(((SAttributeMap)arg).map);
	}
	@Override public int hashCode() { return map.hashCode(); }*/
	
	@Override public Iterable<String> getNames() { return map.keySet(); }
	@Override public boolean isBlob(String name) { return map.get(name).isBlob(); }
	@Override public String getString(String name) {
		if (!map.containsKey(name)) return null;
		return map.get(name).getString();
	}
	@Override public SBlob getBlob(String name) {
		if (!map.containsKey(name)) return null;
		return map.get(name).getBlob();
	}
	
	public void setAttr(String name, SAttribute attr) {
		if (attr == null) map.remove(name);
		else map.put(name, attr);
	}
	public boolean check(SAttributeReader source) {
		Set<String> names = new HashSet<String>();
		for (String name : source.getNames()) names.add(name);
		boolean modified = !map.keySet().equals(names);
		for (Map.Entry<String, SAttribute> entry : map.entrySet()) {
			if (entry.getValue().check(source, entry.getKey())) modified = true;
		}
		return modified;
	}
}
