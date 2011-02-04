package satori.test.meta;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;
import satori.blob.SBlob;
import satori.common.SException;

public class STestMetadata {
	private List<SInputMetadata> inputs = new ArrayList<SInputMetadata>();
	
	STestMetadata() {}
	
	public Iterable<SInputMetadata> getInputs() { return inputs; }
	public void addInput(SInputMetadata im) { inputs.add(im); }
	
	public SAttributeReader getDefaultAttrs() {
		SAttributeMap attrs = SAttributeMap.createEmpty();
		for (SInputMetadata im : inputs) attrs.setAttr(im.getName(), im.getDefaultValue());
		return attrs;
	}
	
	private static final String default_xml =
		"<checker name=\"Default judge\">" +
		"    <input>" +
		"        <value name=\"time\" description=\"Time limit\" required=\"true\"/>" +
		"        <value name=\"memory\" description=\"Memory limit\" required=\"true\" default=\"1073741824\"/>" +
		"        <file name=\"input\" description=\"Input file\" required=\"true\"/>" +
		"        <file name=\"hint\" description=\"Output/hint file\" required=\"false\"/>" +
		"        <file name=\"checker\" description=\"Checker\" required=\"false\"/>" +
		"    </input>" +
		"</checker>";
	
	private static STestMetadata default_meta = null;
	
	public static STestMetadata getDefault() {
		if (default_meta == null) {
			try { default_meta = SXmlParser.parse(default_xml); }
			catch(SXmlParser.ParseException ex) { throw new RuntimeException(ex); }
		}
		return default_meta;
	}
	
	private static Map<String, STestMetadata> meta = new HashMap<String, STestMetadata>();
	
	public static STestMetadata get(SBlob judge) throws SException {
		if (judge == null) return getDefault();
		if (meta.containsKey(judge.getHash())) return meta.get(judge.getHash());
		File file = judge.getFile();
		boolean delete = false;
		if (file == null) {
			try { file = File.createTempFile("judge", null); }
			catch(IOException ex) { throw new SException(ex); }
			judge.saveLocal(file);
			delete = true;
		}
		STestMetadata new_meta = SXmlParser.parseJudge(file);
		if (delete) file.delete();
		meta.put(judge.getHash(), new_meta);
		return new_meta;
	}
}
