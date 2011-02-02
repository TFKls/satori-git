package satori.attribute;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import satori.blob.SBlob;

public class SAttributeMap implements SAttributeReader {
	private Map<String, SAttribute> map;
	
	private SAttributeMap() {}
	
	public static SAttributeMap create(SAttributeReader source) {
		//if (source == null) return null; //TODO: ?
		SAttributeMap self = new SAttributeMap();
		self.map = new HashMap<String, SAttribute>(source.getMap());
		return self;
	}
	public static SAttributeMap createEmpty() {
		SAttributeMap self = new SAttributeMap();
		self.map = new HashMap<String, SAttribute>();
		return self;
	}
	
	public boolean equals(SAttributeMap other) {
		return map.equals(other.map);
	}
	public boolean equals(SAttributeReader other) {
		return map.equals(other.getMap());
	}
	@Override public boolean equals(Object other) {
		if (!(other instanceof SAttributeMap)) return false;
		return equals((SAttributeMap)other);
	}
	@Override public int hashCode() { return map.hashCode(); }
	
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
	@Override public Map<String, SAttribute> getMap() {
		return Collections.unmodifiableMap(map);
	}
	
	public void setAttr(String name, SAttribute attr) {
		if (attr == null) map.remove(name);
		else map.put(name, attr);
	}
}
