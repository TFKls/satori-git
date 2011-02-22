package satori.test.meta;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SException;

public class STestMetadata {
	private List<SInputMetadata> inputs = new ArrayList<SInputMetadata>();
	
	STestMetadata() {}
	
	public List<SInputMetadata> getInputs() { return Collections.unmodifiableList(inputs); }
	public void addInput(SInputMetadata im) { inputs.add(im); }
	
	private static STestMetadata default_meta = new STestMetadata();
	
	public static STestMetadata getDefault() { return default_meta; }
	
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
